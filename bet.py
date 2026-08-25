def compose(category: dict, merchant: dict, trigger: dict, customer: dict | None = None) -> dict:
    m_name = merchant.get('name') or merchant.get('business_name','Merchant')
    m_loc = merchant.get('locality') or merchant.get('city','')
    cat_name = category.get('name','business')
    trig_type = trigger.get('type','') or trigger.get('trigger_type','')
    trig_summary = trigger.get('summary') or trigger.get('title') or trigger.get('reason','')
    trig_summary = str(trig_summary)[:100]

    peer_lift = category.get('peer_stats',{}).get('benchmark','18% more views')
    offer = (merchant.get('active_offers') or merchant.get('offers') or ['Special Offer'])[0]
    if isinstance(offer, dict):
        offer = offer.get('title','Special Offer')

    # Category fit voice
    is_clinical = 'dental' in cat_name.lower() or 'clinic' in cat_name.lower()

    # Trigger-based routing - Section 4 & 10 of brief
    t = trig_type.lower()
    if any(k in t for k in ['profile','incomplete','compliance','verification']):
        body = f"Hi {m_name} from {m_loc} - profile missing {trigger.get('missing_fields','photos/timings')}. {cat_name} stores with complete profiles get {peer_lift}. I can draft it now. Reply 1 to fix, 2 to skip."
    elif 'review' in t:
        body = f"{m_name}, new review: '{trig_summary}'. Quick reply builds trust. Want me to draft a {'clinical' if is_clinical else 'friendly'} reply for your {cat_name} customers? Reply YES/NO."
    elif any(k in t for k in ['festival','weather','heatwave','local','news','event']):
        body = f"{m_name} ({m_loc}) - {trig_summary} trending. Other {cat_name}s are posting now. Your offer '{offer}' fits perfectly. Shall I post for you? Reply 1 yes, 2 later."
    elif customer:
        c_name = customer.get('name','')
        body = f"Hi {c_name}! {m_name} in {m_loc} has {offer} - {trig_summary}. Better than 38% peers. Want to book? Reply BOOK."
    elif 'silent' in t or 'lapsed' in t or 'dormant' in t:
        body = f"{m_name}, no activity in {trigger.get('days_silent','14')} days. Last trigger {trig_summary}. Your {offer} can bring them back. I’ll draft winback msg. Reply 1 to send."
    else:
        body = f"{m_name}, insight: {trig_summary}. Peers saw {peer_lift} lift. Your {cat_name} offer '{offer}' can tap it. I’ll handle post + setup. Reply 1 to go ahead."

    return {
        "suppression_key": f"{merchant.get('id','m')}:{trigger.get('id','t')}",
        "channel": "whatsapp",
        "send_as": "vera",
        "body": body[:300],
        "rationale": f"Trigger={trig_type} + Cat={cat_name} + Merchant={m_name} specificity",
        "personalization": {}
    }