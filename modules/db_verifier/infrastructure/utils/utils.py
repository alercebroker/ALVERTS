def create_base_query(table: str) -> str:
    """Create base query statement for alert ingested on DB.

    Parameters
    ----------
    table : str
        Description of parameter `table`.

    Returns
    -------
    str
        Base query statement to add values format with QUERY % VALUE_STR.

    """
    QUERY = f"""
                WITH batch_candids (oid, candid) AS (
                     VALUES %s
                )
                SELECT batch_candids.oid, batch_candids.candid FROM batch_candids
                LEFT JOIN {table} AS d ON batch_candids.candid = d.candid
                WHERE d.candid IS NULL
            """
    return QUERY

def create_postgresql_connection(user: str, password: str, host: str, database: str, port: int=5432) -> str:
    """Given the DB credentials create connection string.

    Parameters
    ----------
    user : str
        Database user name.
    password : str
        Database password.
    host : str
        Url or IP to connect.
    database : str
        Database name.
    port : int
        Database port (Default:5432).

    Returns
    -------
    type
        Description of returned object.

    """
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
