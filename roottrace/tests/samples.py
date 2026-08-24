"""Regression fixtures: the 10 sample errors, verbatim. Generated, do not hand-edit."""

SAMPLES = {
    1: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/expence_claim_type/filters.py", line 47, in get_expense_claim_type_with_filters
    params = parse_expense_claim_type_filter_params(
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/expence_claim_type/helpers.py", line 377, in parse_expense_claim_type_filter_params
    city_list = _parse_city_filter_value(city)
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/expence_claim_type/helpers.py", line 345, in _parse_city_filter_value
    values = fd.getlist("city[]") or fd.getlist("city") or []
TypeError: 'NoneType' object is not callable
""",
    2: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/mobile_api_v22/domains/api/auth.py", line 90, in login
    login_manager.authenticate(user=user_name, pwd=input_data['password'])
  File "apps/frappe/frappe/auth.py", line 268, in authenticate
    self.fail("Invalid login credentials", user=user.name)
  File "apps/frappe/frappe/auth.py", line 313, in fail
    raise frappe.AuthenticationError
frappe.exceptions.AuthenticationError
""",
    3: r"""
Traceback with variables (most recent call last):
  File "apps/frappe/frappe/desk/doctype/notification_log/notification_log.py", line 40, in after_insert
    send_notification_email(self)
      self = <NotificationLog: cgo53qs0ml>
  File "apps/frappe/frappe/desk/doctype/notification_log/notification_log.py", line 143, in send_notification_email
    frappe.sendmail(
      doc = <NotificationLog: cgo53qs0ml>
      get_url_to_form = <function get_url_to_form at 0x7fcf868205e0>
      strip_html = <function strip_html at 0x7fcf86813d00>
      user = {'email': 'mayur@gmail.com', 'language': 'en'}
      header = 'Assignment Update on SAMP-Mannu--3566'
      email_subject = 'Sample Requested By Sales Person David'
      args = {'body_content': 'Sample Requested By Sales Person David', 'description': 'Review The Sample', 'document_type': 'Sample', 'document_name': 'SAMP-Mannu--3566', 'doc_link': 'http://qa-sigzensfa.sigzenone.com/app/sample/SAMP-Mannu--3566'}
  File "apps/frappe/frappe/__init__.py", line 804, in sendmail
    return builder.process(send_now=now)
      recipients = 'mayur@gmail.com'
      sender = ''
      subject = 'Sample Requested By Sales Person David'
      message = '<p>\n\t<p class="text-color">Sample Requested By Sales Person David</p>\n</p>\n\n<blockquote>\n\t<p>Review The Sample</p>\n\n</blockquote>\n\n<div class="more-info">\n\t<a href="http://qa-sigzensfa.sigzenone.com/app/sample/SAMP-Mannu--3566">Open Document</a>\n</div>'
      as_markdown = False
      delayed = True
      reference_doctype = None
      reference_name = None
      unsubscribe_method = None
      unsubscribe_params = None
      unsubscribe_message = None
      add_unsubscribe_link = 1
      attachments = None
      content = None
      doctype = None
      name = None
      reply_to = None
      queue_separately = False
      cc = []
      bcc = []
      message_id = None
      in_reply_to = None
      send_after = None
      expose_recipients = None
      send_priority = 1
      communication = None
      retry = 1
      now = False
      read_receipt = None
      is_notification = False
      inline_images = None
      template = 'new_notification'
      args = {'body_content': 'Sample Requested By Sales Person David', 'description': 'Review The Sample', 'document_type': 'Sample', 'document_name': 'SAMP-Mannu--3566', 'doc_link': 'http://qa-sigzensfa.sigzenone.com/app/sample/SAMP-Mannu--3566'}
      header = ['Assignment Update on SAMP-Mannu--3566', 'orange']
      print_letterhead = False
      with_container = False
      email_read_tracker_url = None
      x_priority = 3
      email_headers = None
      text_content = None
      QueueBuilder = <class 'frappe.email.doctype.email_queue.email_queue.QueueBuilder'>
      builder = <frappe.email.doctype.email_queue.email_queue.QueueBuilder object at 0x7fcf82500e20>
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 746, in process
    queue_data = self.as_dict(include_recipients=False)
      self = <frappe.email.doctype.email_queue.email_queue.QueueBuilder object at 0x7fcf82500e20>
      send_now = False
      final_recipients = ['mayur@gmail.com']
      queue_separately = False
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 788, in as_dict
    email_account = self.get_outgoing_email_account()
      self = <frappe.email.doctype.email_queue.email_queue.QueueBuilder object at 0x7fcf82500e20>
      include_recipients = False
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 646, in get_outgoing_email_account
    self._email_account = EmailAccount.find_outgoing(
      self = <frappe.email.doctype.email_queue.email_queue.QueueBuilder object at 0x7fcf82500e20>
  File "apps/frappe/frappe/email/doctype/email_account/email_account.py", line 42, in wrapper_cache_email_account
    matched_accounts = func(*args, **kwargs)
      args = (<class 'frappe.email.doctype.email_account.email_account.EmailAccount'>,)
      kwargs = {'match_by_doctype': None, 'match_by_email': '', '_raise_error': True}
      match_by = [None, '', True, 'default']
      matched_accounts = []
      cached_accounts = {}
      cache_name = 'outgoing_email_account'
      func = <function EmailAccount.find_outgoing at 0x7fcf74a092d0>
  File "apps/frappe/frappe/email/doctype/email_account/email_account.py", line 402, in find_outgoing
    frappe.throw(
      cls = <class 'frappe.email.doctype.email_account.email_account.EmailAccount'>
      match_by_email = ''
      match_by_doctype = None
      _raise_error = True
      doc = False
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
      msg = 'Please setup default outgoing Email Account from Tools > Email Account'
      exc = <class 'frappe.exceptions.OutgoingEmailError'>
      title = None
      is_minimizable = False
      wide = False
      as_list = False
      primary_action = None
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
      title = None
      as_table = False
      as_list = False
      indicator = 'red'
      alert = False
      primary_action = None
      is_minimizable = False
      wide = False
      realtime = False
      sys = <module 'sys' (built-in)>
      _raise_exception = <function msgprint.<locals>._raise_exception at 0x7fcf74936050>
      inspect = <module 'inspect' from '/usr/lib/python3.10/inspect.py'>
      msg = 'Please setup default outgoing Email Account from Tools > Email Account'
      out = {'message': 'Please setup default outgoing Email Account from Tools > Email Account', 'title': 'Message', 'indicator': 'red', 'raise_exception': 1, '__frappe_exc_id': 'bb48d537c8ab5c4aa2aa34feb2c3e74eddf18b68fe88233ed4963df5'}
      raise_exception = <class 'frappe.exceptions.OutgoingEmailError'>
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
      exc = OutgoingEmailError('Please setup default outgoing Email Account from Tools > Email Account')
      inspect = <module 'inspect' from '/usr/lib/python3.10/inspect.py'>
      msg = 'Please setup default outgoing Email Account from Tools > Email Account'
      out = {'message': 'Please setup default outgoing Email Account from Tools > Email Account', 'title': 'Message', 'indicator': 'red', 'raise_exception': 1, '__frappe_exc_id': 'bb48d537c8ab5c4aa2aa34feb2c3e74eddf18b68fe88233ed4963df5'}
      raise_exception = <class 'frappe.exceptions.OutgoingEmailError'>
frappe.exceptions.OutgoingEmailError: Please setup default outgoing Email Account from Tools > Email Account
""",
    4: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/tour/crud.py", line 469, in add_customer_lead_opportunity
    assert_prior_party_rows_have_type_of_activity(
  File "apps/sigzensfa/sigzensfa/sfa_tour/doctype/field_activity/field_activity.py", line 53, in assert_prior_party_rows_have_type_of_activity
    frappe.throw(
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
frappe.exceptions.ValidationError: Please select Type Of Activity for existing Customer <strong>CU-00021</strong> before adding another entry for the same Customer.
""",
    5: r"""
Traceback with variables (most recent call last):
  File "apps/frappe/frappe/app.py", line 115, in application
    response = frappe.api.handle(request)
      request = <Request 'https://qa-varmora15.sigzenone.com/api/method/sfa_sigzen.mobile_api.stock_report.stock_report?item=S-OPC-071044&product_category=SANITARYWARE&product_group=ONE%20PIECE%20CLOSETS&product_family=&product_series=&product_finish=' [GET]>
      response = None
      rollback = True
      e = TypeError("unsupported operand type(s) for +: 'NoneType' and 'str'")
  File "apps/frappe/frappe/api/__init__.py", line 49, in handle
    data = endpoint(**arguments)
      request = <Request 'https://qa-varmora15.sigzenone.com/api/method/sfa_sigzen.mobile_api.stock_report.stock_report?item=S-OPC-071044&product_category=SANITARYWARE&product_group=ONE%20PIECE%20CLOSETS&product_family=&product_series=&product_finish=' [GET]>
      endpoint = <function handle_rpc_call at 0x7fbddbc9e3b0>
      arguments = {'method': 'sfa_sigzen.mobile_api.stock_report.stock_report'}
  File "apps/frappe/frappe/api/v1.py", line 36, in handle_rpc_call
    return frappe.handler.handle()
      method = 'sfa_sigzen.mobile_api.stock_report.stock_report'
      frappe = <module 'frappe' from 'apps/frappe/frappe/__init__.py'>
  File "apps/frappe/frappe/handler.py", line 51, in handle
    data = execute_cmd(cmd)
      cmd = 'sfa_sigzen.mobile_api.stock_report.stock_report'
      data = None
  File "apps/frappe/frappe/handler.py", line 84, in execute_cmd
    return frappe.call(method, **frappe.form_dict)
      cmd = 'sfa_sigzen.mobile_api.stock_report.stock_report'
      from_async = False
      server_script = None
      method = <function stock_report at 0x7fbdc70a9240>
  File "apps/frappe/frappe/__init__.py", line 1754, in call
    return fn(*args, **newargs)
      fn = <function stock_report at 0x7fbdc70a9240>
      args = ()
      kwargs = {'item': 'S-OPC-071044', 'product_category': 'SANITARYWARE', 'product_group': 'ONE PIECE CLOSETS', 'product_family': '', 'product_series': '', 'product_finish': '', 'cmd': 'sfa_sigzen.mobile_api.stock_report.stock_report'}
      newargs = {'item': 'S-OPC-071044', 'product_category': 'SANITARYWARE', 'product_group': 'ONE PIECE CLOSETS', 'product_family': '', 'product_series': '', 'product_finish': ''}
  File "apps/frappe/frappe/utils/typing_validations.py", line 32, in wrapper
    return func(*args, **kwargs)
      args = ()
      kwargs = {'item': 'S-OPC-071044', 'product_category': 'SANITARYWARE', 'product_group': 'ONE PIECE CLOSETS', 'product_family': '', 'product_series': '', 'product_finish': ''}
      apply_condition = <function whitelist.<locals>.innerfn.<locals>.<lambda> at 0x7fbdc70a9360>
      func = <function stock_report at 0x7fbdc70a9510>
  File "apps/sfa_sigzen/sfa_sigzen/mobile_api/stock_report.py", line 47, in stock_report
    stock_report = requests.get(url=url_doc("base_url_stock")+"StockByBathwareProductId", params=params, headers= {"apiKey": url_doc("encrypted_api_key_stock")})
      product_category = 'SANITARYWARE'
      product_group = 'ONE PIECE CLOSETS'
      product_family = ''
      product_series = ''
      product_finish = ''
      item = 'S-OPC-071044'
      item_status = ''
      stock_data = None
      user = 'se-02011@sfa.com'
      division = 'BATHWARE-DOMESTIC'
      params = {'productId': 'S-OPC-071044'}
builtins.TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
""",
    6: r"""
Traceback (most recent call last):
  File "apps/sigzen_whatsapp/sigzen_whatsapp/install.py", line 91, in create_doctype_data
    custom_data.save()
  File "apps/frappe/frappe/model/document.py", line 378, in save
    return self._save(*args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 417, in _save
    self._validate()
  File "apps/frappe/frappe/model/document.py", line 624, in _validate
    self._validate_selects()
  File "apps/frappe/frappe/model/base_document.py", line 913, in _validate_selects
    frappe.throw(
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
frappe.exceptions.ValidationError:  Template Type cannot be "document". It should be one of "Text", "Image", "Video", "Document", "Carousel", "Location"
""",
    7: r"""
Traceback (most recent call last):
  File "apps/sigzen_whatsapp/sigzen_whatsapp/meta_whatsapp_campagin/events/event.py", line 501, in create_campaign_doctype_area
    send_coupon_code(doc, routes)
  File "apps/sigzen_whatsapp/sigzen_whatsapp/meta_whatsapp_campagin/events/event.py", line 516, in send_coupon_code
    template_doc = frappe.get_doc("Template",routes.custom_whatsapp_verification_coupon_code)
AttributeError: 'WebPage' object has no attribute 'custom_whatsapp_verification_coupon_code'
""",
    8: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/field_activity/tour_parties.py", line 16, in customer_list
    list = get_customer_list(tour_plan_id)
  File "apps/sigzensfa/sigzensfa/mobile_api_v24/domains/field_activity/tour_parties.py", line 28, in get_customer_list
    tour_plan_doc = frappe.get_doc('Tour Plan', tour_plan_id)
  File "apps/frappe/frappe/__init__.py", line 1308, in get_doc
    return frappe.model.document.get_doc(*args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 85, in get_doc
    return controller(*args, **kwargs)
  File "apps/frappe/frappe/model/document.py", line 126, in __init__
    self.load_from_db()
  File "apps/frappe/frappe/model/document.py", line 179, in load_from_db
    frappe.throw(
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
frappe.exceptions.DoesNotExistError: Tour Plan undefined not found
""",
    9: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/events/approval_notifications.py", line 42, in notify
    frappe.sendmail(
  File "apps/frappe/frappe/__init__.py", line 804, in sendmail
    return builder.process(send_now=now)
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 746, in process
    queue_data = self.as_dict(include_recipients=False)
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 788, in as_dict
    email_account = self.get_outgoing_email_account()
  File "apps/frappe/frappe/email/doctype/email_queue/email_queue.py", line 646, in get_outgoing_email_account
    self._email_account = EmailAccount.find_outgoing(
  File "apps/frappe/frappe/email/doctype/email_account/email_account.py", line 42, in wrapper_cache_email_account
    matched_accounts = func(*args, **kwargs)
  File "apps/frappe/frappe/email/doctype/email_account/email_account.py", line 402, in find_outgoing
    frappe.throw(
  File "apps/frappe/frappe/__init__.py", line 609, in throw
    msgprint(
  File "apps/frappe/frappe/__init__.py", line 574, in msgprint
    _raise_exception()
  File "apps/frappe/frappe/__init__.py", line 525, in _raise_exception
    raise exc
frappe.exceptions.OutgoingEmailError: Please setup default outgoing Email Account from Tools > Email Account
""",
    10: r"""
Traceback (most recent call last):
  File "apps/sigzensfa/sigzensfa/mobile_api/domains/tour/lookups.py", line 117, in tour_type_list
    tour_type=frappe.db.get_list("Tour Type",['tour_type','allow_party_selection'])
  File "apps/frappe/frappe/database/database.py", line 760, in get_list
    return frappe.get_list(*args, **kwargs)
  File "apps/frappe/frappe/__init__.py", line 2021, in get_list
    return frappe.model.db_query.DatabaseQuery(doctype).execute(*args, **kwargs)
  File "apps/frappe/frappe/model/db_query.py", line 114, in execute
    self.check_read_permission(self.doctype, parent_doctype=parent_doctype)
  File "apps/frappe/frappe/model/db_query.py", line 513, in check_read_permission
    self._set_permission_map(doctype, parent_doctype)
  File "apps/frappe/frappe/model/db_query.py", line 519, in _set_permission_map
    frappe.has_permission(
  File "apps/frappe/frappe/__init__.py", line 1065, in has_permission
    raise frappe.PermissionError
frappe.exceptions.PermissionError





here i am suggest one thing also check how frappe generates error and display, according to that make app robust and 100% accurate so anyone can solve any error in live, qa ..
""",
}
