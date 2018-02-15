# Redshift Unload

This script is meant to simplify extracting tables from <a href="https://openbridge.com/warehouse/amazon-redshift" target="_blank">Redshift</a> by running a pre-packaged [`UNLOAD` command](http://docs.aws.amazon.com/redshift/latest/dg/r_UNLOAD.html) which solves the feature gap of the `UNLOAD` command not including a header row. This Docker-based script will retrieve and adds headers to the file before output.

## Requirements

Everything is built into the container, including [`psycopg2`](http://initd.org/psycopg/docs/install.html) and other OS and Python packages. You will need to have connection details to your Redshift host and the AWS credentials in your environmental variables to write the `UNLOADED` data to an S3 bucket.

## Installing

To get the image, you need to have Docker installed and authenticate with he registry.

Once installed, you can get the image by pulling from [`Artifactory`](https://artifactory.gameofloans.com/)

  1. Authenticating to the docker registry as detailed on the wiki https://confluence.gameofloans.com/display/ENG/Artifactory+User+Guide#ArtifactoryUserGuide-Authentication.1

  2. Run in terminal
```bash
docker pull docker.gameofloans.com/datascience/redshift-unload:latest
```

## Environment Variables

For security purposes, your Redshift AWS credentials must be stored in the following environmental variables:

* ``DB_HOST``
* ``DB_PORT``
* ``DB_DATABASE``
* ``DB_USER``
* ``DB_PASSWORD``
* ``AWS_ACCESS_KEY_ID``
* ``AWS_SECRET_ACCESS_KEY``

## Runtime Parameters

The script can accept different runtime parameters:

* ``-t``: The table you wish to UNLOAD
* ``-f``: The S3 key at which the file will be placed
* ``-c``: (Optional) The schema which the table resides in. If left blank, the script will default to "public".
* ``-s`` (Optional): The file you wish to read a custom valid SQL WHERE clause from. This will be sanitized then inserted into the UNLOAD command.
* ``-r`` (Optional): The range column you wish to use to constrain the results. Any type supported by Redshift's [BETWEEN function](http://docs.aws.amazon.com/redshift/latest/dg/r_range_condition.html) is accepted here (date, integer, etc.)
* ``-r0`` (Optional): The desired start range to constrain the result set
* ``-r1`` (Optional): The desired end range to constrain the result set  
Note:  ``-s`` and ``-d`` are mutually exlusive and cannot be used together. If neither is used, the script will default to not specifying a WHERE clause and output the entire table.

## Helper Function

If you are UNLOADing frequently from Redshift, it would be wise to alias a helper function in your environment. 

Data Science Configuration:

```
alias redshift_unload = 'docker run --rm -i \
-e DB_HOST=$DB_HOST \
-e DB_PORT=$DB_PORT \
-e DB_DATABASE=$DB_DATABASE \
-e DB_USER=$DB_USER \
-e DB_PASSWORD=$DB_PASSWORD \
-e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
-e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
docker.gameofloans.com/datascience/redshift-unload:latest $@'
```

## Running An Extract

This command will unload the data in the table ``my_redshift_table `` under the ``scratch`` schema by using the ``submittedat`` field for the first half of 2017 to a specified S3 location.

Running via the `Helper Function`:

```bash
redshift_unload \
-t my_redshift_table -c scratch \
-f s3://com.lendup.dev.datascience/my_redshift_table.csv \
-r submittedat -r0 2017-01-01 -r1 2017-06-30
```

## The `-s` Option
As mentioned previously, it is possible to supply your own WHERE clause to be used in the UNLOAD command. This is done via an external SQL file.

**Example:**
To use this functionality to UNLOAD only new users, you create a SQL file called `new_users.sql` that contains ``WHERE is_new = true``

```bash
redshift_unload \
-t my_redshift_table -c scratch \
-f s3://com.lendup.dev.datascience/my_redshift_table.csv \
-r submittedat -r0 2017-01-01 -r1 2017-06-30 \
-s /new_users.sql
```

**NOTE**: The -s option will **only** work for the `WHERE` clause. If you try other clauses it will fail


## What's Next?

* Supply the query instead of a table name
* Multiple filters from command line
* Easier method to specify file output location on S3
