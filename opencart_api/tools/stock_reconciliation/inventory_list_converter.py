import sys
import getopt
import os
import csv


def process(input_file, input_erpnext_file, output_erpnext_file):
    item_code_to_quantity = {}
    skipped_count = 0
    skipped_rows = []
    with open(input_file, 'rb') as in_file:
        all_rows = csv.reader(in_file, delimiter=',')
        for row in all_rows:
            item_code = row[1]
            try:
                quantity = float(row[3].strip().replace(',', ''))
            except:
                skipped_count += 1
                skipped_rows.append(','.join(row))
                continue
            # Description,Item No.,Unit,Quantity,Minimum,On Purchase Order,On Sales Order,To Order
            item_code_to_quantity[item_code.lower()] = quantity
            print('%s  %s' % (item_code, quantity))
    print('\n\nSkipped rows count: %d\nSkipped rows \n%s' % (skipped_count, '\n'.join(skipped_rows)))

    if os.path.exists(output_erpnext_file):
        print('"%s" file already exists. Move or rename this file and try again.' % output_erpnext_file)
        exit(0)
    with open(input_erpnext_file, 'rb') as in_erpnext_file:
        reader = csv.reader(in_erpnext_file, delimiter=',')
        with open(output_erpnext_file, 'wb') as out_erpnext_file:
            writer = csv.writer(out_erpnext_file, delimiter=',')
            for row in reader:
                # item_code,oc_item_name,oc_model,warehouse,qty,valuation_rate,current_qty,current_valuation_rate
                if row and row[0].startswith('ITEM-'):
                    oc_model = row[2]
                    quantity = item_code_to_quantity.get(oc_model.lower())
                    if quantity is not None:
                        row[4] = quantity
                        writer.writerow(row)
                    else:
                        continue
                else:
                    writer.writerow(row)


def main(argv):
    input_file = ''
    input_erpnext_file = ''
    output_erpnext_file = ''
    try:
        opts, args = getopt.getopt(argv, '', ['input=', 'input_erpnext=', 'output_erpnext='])
    except getopt.GetoptError:
        print('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <input file> -ie <input erpnext file> -oe <output erpnext file>')
            sys.exit()
        elif opt in ('--input',):
            input_file = arg
        elif opt in ('--input_erpnext',):
            input_erpnext_file = arg
        elif opt in ('--output_erpnext',):
            output_erpnext_file = arg
    print('Input file is "%s"' % input_file)
    print('Input ERPNext template is "%s"' % input_erpnext_file)
    print('Output ERPNext template is "%s"' % output_erpnext_file)
    if input_file and input_erpnext_file and output_erpnext_file:
        process(input_file, input_erpnext_file, output_erpnext_file)
    else:
        print('Please specify inputfile and outputfile')


if __name__ == '__main__':
    main(sys.argv[1:])
