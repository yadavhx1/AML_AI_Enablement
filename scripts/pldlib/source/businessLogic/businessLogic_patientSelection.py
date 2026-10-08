def business_logic(spark,
                     criteria_name=[],
                     index_date=[],
                     period_start=[],
                     period_end=[],
                     cutoff_criteria=[],
                     level_column=[],
                     date_cmp_clm=[],
                     filters=[],
                     agg_func=[]):
    df = {}
    for i in range(0, 2):
        active_criteria = [criteria_name[i]]
        rest_criteria = list(set(criteria_name) - set(active_criteria))
        level1 = ''

        for j in range(0, len(rest_criteria)):
            if (j == 0):
                level1 = level1 + "0 as " + rest_criteria[j]


            else:
                level1 = level1 + ",0 as " + rest_criteria[j]
    df[i] = spark.sql('''SELECT PATIENT_GID, 
        case when 
        {agg_func}(CASE WHEN {level_column} = '{filters}' then 1 else 0 end) > {cutoff_criteria} then 1 else 0 end as {active_criteria}, {level1}
    	from (

        select patient_gid,{level_column}
        from (

        select patient_gid,{level_column},{date_cmp_clm},add_months(from_unixtime(unix_timestamp('{index_date}','mm/DD/yyyy'),'YYYY-mm-DD'),{period_start})
         as Period_start, add_months(from_unixtime(unix_timestamp('{index_date}','mm/DD/yyyy'),'YYYY-mm-DD'),{period_end}) as
         period_end 
    	 from apld_sha_ptd_immunology_work.MABI_TX_VW  A

        ) A
        where {date_cmp_clm} between period_start and period_end)
        B
        group by patient_gid'''.format(agg_func=agg_func[i], level_column=level_column[i], filters=filters[i],
                                       cutoff_criteria=cutoff_criteria[i], index_date=index_date[i],
                                       active_criteria=active_criteria[0], period_start=period_start[i],
                                       period_end=period_end[i], date_cmp_clm=date_cmp_clm[i], level1=level1))

    print(df)

    for k in range(1, 2):
        df[0] = df[0].select("PATIENT_GID", "criteria_1", "criteria_2", "criteria_3").unionAll(
            df[k].select("PATIENT_GID", "criteria_1", "criteria_2", "criteria_3"))
    columns = df[0].columns

    max_columns = ''

    for i in range(0, len(criteria_name)):
        if (i == 0):
            max_columns = max_columns + "max(" + criteria_name[i] + ") as " + criteria_name[i]


        else:
            max_columns = max_columns + ",max(" + criteria_name[i] + ") as " + criteria_name[i]

    df[0].createOrReplaceTempView('temp')

    return df[0]
