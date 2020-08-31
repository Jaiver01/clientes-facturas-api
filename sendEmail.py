import smtplib
import email.message
from email.mime.text import MIMEText

def sendEmail(client, state):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('pcpruebacorreo44@gmail.com', 'pass77--')

    content = ''
    for invoice in client['invoices']:
        iva = invoice['total'] * 0.19
        subTotal = invoice['total'] - iva

        content += '<tr>'
        content += '<td align="center">' + invoice['code'] + '</td>'
        content += '<td align="right">$ ' + str(invoice['total']) + '</td>'
        content += '<td align="right">$ ' + str(subTotal) + '</td>'
        content += '<td align="right">$ ' + str(iva) + '</td>'
        content += '<td align="right">$ ' + str(invoice['withholdingTax']) + '</td>'
        content += '<td align="center">' + invoice['date'].strftime("%Y/%m/%d %H:%M") + '</td>'
        content += '<td>' + state + '</td>'
        content += '<td align="center">' + ('Pagada' if invoice['paid'] else 'Debe') + '</td>'
        content += '</tr>'

    content = """Estimado(a): <b>%s</b><br><br>
    Las siguientes facturas han pasado a %s:<br>
    <table border='1' cellpadding='3'>
        <tr>
            <th><b>Codigo</b></th>
            <th><b>Total</b></th>
            <th><b>Subtotal</b></th>
            <th><b>IVA</b></th>
            <th><b>Retencion</b></th>
            <th><b>Fecha</b></th>
            <th><b>Estado</b></th>
            <th><b>Pagada</b></th>
        </tr>
        %s
    </table>
    """ % (client['name'], state, content)

    msg = email.message.Message()
    msg['Subject'] = 'Se ha cambiado el estado a ' + state
    msg['From'] = 'Pruebas <pcpruebacorreo44@gmail.com>'
    msg['To'] = client['email']
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(content)

    server.sendmail('pcpruebacorreo44@gmail.com', client['email'], msg.as_string())

    server.quit()