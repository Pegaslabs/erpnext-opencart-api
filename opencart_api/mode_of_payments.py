
PAYMENT_METHODS_CODES = ('pp_express', 'cheque', 'stripe')


POS_PAYMENT_METHODS_CODES = ('pp_express', 'stripe')


def is_pos_payment_method(code):
    return code in POS_PAYMENT_METHODS_CODES
