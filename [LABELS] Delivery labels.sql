SELECT 
    o.id as order_id,
    o.delivery_tour_index as shipping_group,
    o.delivery_tour_order_id as shipping_order,
    'BE_' || o.id as qrcode_data,
    s.total_meals as total_meals,
    o.max_meals,
    ceil(s.total_meals::numeric / 7)::numeric::integer as labels_quantity,
    o.shipping_date::TEXT as shipping_date,
    'color_' || ((o.delivery_tour_index % 10) + 1)::TEXT as color,
    upper(u.language_code) as user_lang,
    INITCAP(u.first_name || ' ' || u.last_name) as cust_name,
    o.delivery_planning_name as shipping_label,
    d.status = 'replacement' as delivery_status
FROM account_order o
INNER JOIN account_user u ON o.user_id = u.id
INNER JOIN (
    SELECT order_id, sum(quantity) as total_meals
    FROM account_selection
    GROUP BY order_id
) s ON s.order_id = o.id
LEFT JOIN account_delivery d ON o.delivery_id = d.id
WHERE o.is_active = TRUE
    AND o.is_closed = TRUE
    AND o.user_id IS NOT NULL
    AND (
        CASE EXTRACT(DOW FROM CURRENT_DATE)
            WHEN 5 THEN o.shipping_date = CURRENT_DATE + INTERVAL '1 day'  -- Vendredi → Samedi
            WHEN 6 THEN o.shipping_date BETWEEN CURRENT_DATE + INTERVAL '1 day' AND CURRENT_DATE + INTERVAL '3 days'  -- Samedi → Dimanche à Mardi
            ELSE o.shipping_date = CURRENT_DATE
        END
    )
ORDER BY 
    o.shipping_date, 
    o.delivery_planning_name, 
    o.delivery_tour_index, 
    o.shipping_time;
