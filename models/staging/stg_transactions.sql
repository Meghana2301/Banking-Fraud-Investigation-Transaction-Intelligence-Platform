with scored as (
    select
        transaction_id,
        customer_id,
        account_id,
        timestamp as transaction_timestamp,
        cast(timestamp as date) as transaction_date,
        amount,
        lower(merchant_category) as merchant_category,
        upper(country) as country,
        lower(channel) as channel,
        is_fraud,
        least(
            case when amount >= 1000 then 50 when amount >= 500 then 25 else 0 end
            + case when country <> 'US' then 30 else 0 end
            + case when channel = 'online' then 15 else 0 end,
            100
        ) as risk_score
    from {{ source('raw', 'transactions') }}
)
select *, iff(risk_score >= 65, 1, 0) as flagged
from scored
