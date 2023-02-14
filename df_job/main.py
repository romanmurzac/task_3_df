import argparse
import json
from datetime import datetime

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

SCHEMA = ",".join(
    [
        "StudentName:STRING",
        "StudyYear:INTEGER",
        "AverageGrade:FLOAT64",
        "RecordTime:TIMESTAMP",
    ]
)

ERROR_SCHEMA = ",".join(
    [
        "message:STRING",
        "timestamp:TIMESTAMP",
    ]
)


class Parser(beam.DoFn):
    ERROR_TAG = 'error'

    def process(self, line):
        try:
            data_row = json.loads(line.decode("utf-8"))
            if not ("StudyYear" in data_row or "AverageGrade" in data_row):
                raise ValueError('Missing required parameters: "StudyYear" and "AverageGrade"')
            data_row["RecordTime"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            yield data_row
        except Exception as error:
            error_row = {"Message": str(error), "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            yield beam.pvalue.TaggedOutput(self.ERROR_TAG, error_row)


def run(options, input_subscription, output_success_table, output_error_table):
    with beam.Pipeline(options=options) as pipeline:
        rows, error_rows = \
            (pipeline | 'Read from PubSub' >> beam.io.ReadFromPubSub(subscription=input_subscription)
             | 'Parse JSON messages' >> beam.ParDo(Parser()).with_outputs(Parser.ERROR_TAG, main='rows')
             )

        _ = (rows | 'Write data to BigQuery'
             >> beam.io.WriteToBigQuery(output_success_table,
                                        create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                                        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                                        schema=SCHEMA
                                        )
             )

        _ = (error_rows | 'Write errors to BigQuery'
             >> beam.io.WriteToBigQuery(output_error_table,
                                        create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                                        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                                        schema=ERROR_SCHEMA
                                        )
             )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--job_name',
        required=True,
        default="dataflow-gcp-srp-hw",
        help='Dataflow job name.'
    )
    parser.add_argument(
        '--project',
        required=True,
        default="project-gcp-srp-hw",
        help='Project name.'
    )
    parser.add_argument(
        '--region',
        required=True,
        default="US",
        help='Project region.'
    )
    parser.add_argument(
        '--input_subscription',
        required=True,
        default="/subscriptions/project-gcp-srp-hw/subscription-gcp-srp-hw",
        help='Input PubSub subscription.'
    )
    parser.add_argument(
        '--output_success_table',
        required=True,
        default="project-gcp-srp-hw:df_dataset_gcp_srp_hw.table-gcp-srp-hw-success",
        help='Output BigQuery table for success data.'
    )
    parser.add_argument(
        '--output_error_table',
        required=True,
        default="project-gcp-srp-hw:df_dataset_gcp_srp_hw.table-gcp-srp-hw-error",
        help='Output BigQuery table for error data.'
    )
    parser.add_argument(
        '--template_location',
        required=True,
        default="gs://project-gcp-srp-hw-bucket-gcp-srp-hw/templates/dataflow-job",
        help='Templates location.'
    )
    parser.add_argument(
        '--staging_location',
        required=True,
        default="gs://project-gcp-srp-hw-bucket-gcp-srp-hw/temp_dir",
        help='Staging location.'
    )
    parser.add_argument(
        '--temp_location',
        required=True,
        default="gs://project-gcp-srp-hw-bucket-gcp-srp-hw/temp_dir",
        help='Temporary location.'
    )
    parser.add_argument(
        '--runner',
        required=True,
        default="DataflowRunner",
        help='Runner.'
    )
    parser.add_argument(
        '--setup_file',
        required=True,
        default="df_job/setup.py",
        help='Setup file.'
    )

    args = parser.parse_args()
    pipeline_options = {'project': args.project, 'runner': args.runner, 'region': args.region,
                        'staging_location': args.staging_location, 'temp_location': args.temp_location,
                        'template_location': args.template_location, 'save_main_session': True, 'streaming': True,
                        'job_name': args.job_name, }
    pipeline_options = PipelineOptions.from_dictionary(pipeline_options)

    run(
        pipeline_options,
        args.input_subscription,
        args.output_success_table,
        args.output_error_table
    )
