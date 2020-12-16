import imgkit, platform, os, uuid, shutil, oss2
from jinrui.config.secret import ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET
pdf_uuid = str(uuid.uuid1())
if platform.system() == "Windows":
    pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
else:
    pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
if not os.path.exists(pdf_path):
    os.makedirs(pdf_path)
test_html = """
<!DOCTYPE html>
<html>
   <head>
      <meta charset="UTF-8">
      <title>Shipper Demo</title>
   </head>
    <body style="width:820px;height:1160px">
        <table style="width:820px" cellpadding="2" cellspacing="0" border="0">
            <tr>
                <td colspan="4"><span><strong>{0}</strong></span></td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>ACCEPTANCE CHECKLIST FOR DRY ICE (Carbon Dioxide, solid)</strong></span></td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>(For use when a Shipper's Declaration</strong></span></td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>for Dangerous Goods is not required)</strong></span></td>
            </tr>
            <tr>
                <td colspan="4"><span>A checklist is required for all shipments of dangerous goods (9.1.4) to enable proper
                    acceptance checks to be made. The following example checklist is provided to assist shippers and
                    carriers with the acceptance of dry ice when packaged on its own or with non-dangerous goods.</span></td>
            </tr>
            <tr>
                <td colspan="4"><span>Is the following information correct for each entry?</span></td>
            </tr>
        </table>
        <table style="width:820px" cellpadding="2" cellspacing="0" border="1">
            <tr>
                <td colspan="4"><span><strong>DOCUMENTATION</strong></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <br/>
                </td>
                <td style="width:5%">
                    <span><strong>YES</strong></span>
                </td>
                <td style="width:5%">
                    <span><strong>No*</strong></span>
                </td>
                <td style="width:5%">
                    <span><strong>N/A</strong></span>
                </td>
            </tr>
            <tr>
                <td style="width:85%" colspan="4">
                    <span>The Air Waybill contains the following information in the “Nature and Quantity of Goods” box [8.2.3]</span>
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>1. “UN1845”</span>
                </td>
                <td style="width:5%">
                    {1}
                </td>
                <td style="width:5%">
                    {2}
                </td>
                <td style="width:5%">
                    {3}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>2. The words “Carbon dioxide, solid” or “Dry ice”</span>
                </td>
                <td style="width:5%">
                    {4}
                </td>
                <td style="width:5%">
                    {5}
                </td>
                <td style="width:5%">
                    {6}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>3. Number of packages (unless these are the only packages within the consignment)</span>
                </td>
                <td style="width:5%">
                    {7}
                </td>
                <td style="width:5%">
                    {8}
                </td>
                <td style="width:5%">
                    {9}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>4. The net weight of dry ice in kilograms</span>
                </td>
                <td style="width:5%">
                    {10}
                </td>
                <td style="width:5%">
                    {11}
                </td>
                <td style="width:5%">
                    {12}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>Quantity</strong></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>5. The quantity of dry ice per package is 200 kg or less [4.2]</span>
                </td>
                <td style="width:5%">
                    {13}
                </td>
                <td style="width:5%">
                    {14}
                </td>
                <td style="width:5%">
                    {15}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>PACKAGES AND OVERPACKS</strong></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>6. Same number of packages as shown on the Air Waybill</span>
                </td>
                <td style="width:5%">
                    {16}
                </td>
                <td style="width:5%">
                    {17}
                </td>
                <td style="width:5%">
                    {18}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>7. Packages free from damage and leakage</span>
                </td>
                <td style="width:5%">
                    {19}
                </td>
                <td style="width:5%">
                    {20}
                </td>
                <td style="width:5%">
                    {21}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>8. The packaging conforms with Packing Instruction 954 and the package is vented to permit the release of gas</span>
                </td>
                <td style="width:5%">
                    {22}
                </td>
                <td style="width:5%">
                    {23}
                </td>
                <td style="width:5%">
                    {24}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>Marks & Labels</strong></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>9. “UN1845” marked [7.1.4.1(a)]</span>
                </td>
                <td style="width:5%">
                    {25}
                </td>
                <td style="width:5%">
                    {26}
                </td>
                <td style="width:5%">
                    {27}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>10. The words “Carbon dioxide, solid” or “Dry ice” [7.1.4.1(a)]</span>
                </td>
                <td style="width:5%">
                    {28}
                </td>
                <td style="width:5%">
                    {29}
                </td>
                <td style="width:5%">
                    {30}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>11. Full name and address of the shipper and consignee [7.1.4.1(b)]</span>
                </td>
                <td style="width:5%">
                    {31}
                </td>
                <td style="width:5%">
                    {32}
                </td>
                <td style="width:5%">
                    {33}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><i><strong>Note: </strong>
                    The name and address of the shipper and consignee marked on the package may differ from that on the AWB.</i></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>12. The net weight of dry ice within each package [7.1.4.1(d)]</span>
                </td>
                <td style="width:5%">
                    {34}
                </td>
                <td style="width:5%">
                    {35}
                </td>
                <td style="width:5%">
                    {36}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>13. Class 9 label properly affixed [7.2.3.9, 7.2.6]</span>
                </td>
                <td style="width:5%">
                    {37}
                </td>
                <td style="width:5%">
                    {38}
                </td>
                <td style="width:5%">
                    {39}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>14. Irrelevant marks and labels removed or obliterated [7.1.1(b); 7.2.1(a)]</span>
                </td>
                <td style="width:5%">
                    {40}
                </td>
                <td style="width:5%">
                    {41}
                </td>
                <td style="width:5%">
                    {42}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><i><strong>Note: </strong>
                    The Marking and labelling requirements do not apply to ULDs containing dry ice</i></span></td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>For Overpacks</strong></span></td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>15. Packaging Use marks and hazard and handling labels,
                        as required must be clearly visible or reproduced on the outside of the overpack [7.1.7.1, 7.2.7]</span>
                </td>
                <td style="width:5%">
                    {43}
                </td>
                <td style="width:5%">
                    {44}
                </td>
                <td style="width:5%">
                    {45}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>16. The word “Overpack” marked if marks and labels are not visible on packages within the overpack [7.1.7.1]</span>
                </td>
                <td style="width:5%">
                    {46}
                </td>
                <td style="width:5%">
                    {47}
                </td>
                <td style="width:5%">
                    {48}
                </td>
            </tr>
            <tr>
                <td style="width:85%">
                    <span>17. The total net weight of carbon dioxide, solid (dry ice) in the overpack [7.1.7.1]</span>
                </td>
                <td style="width:5%">
                    {49}
                </td>
                <td style="width:5%">
                    {50}
                </td>
                <td style="width:5%">
                    {51}
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><i><strong>Note: </strong>
                    The Marking and labelling requirements do not apply to ULDs containing dry ice</i></span></td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>State and Operator Variations</strong></span></td>
            </tr>
            <tr>
               <td style="width:85%">
                    <span>18. State and operator variations complied with [2.8]</span>
                </td>
                <td style="width:5%">
                    {52}
                </td>
                <td style="width:5%">
                    {53}
                </td>
                <td style="width:5%">
                    {54}
                </td>
            </tr>
            <tr>
                <td style="width:100%" colspan="4">
                    <span>Comments:___________________________________________________</span>
                </td>
            </tr>
            <tr>
                <td style="width:100%" colspan="4">
                    <span>Checked by:<u>{55}</u></span>
                </td>
            </tr>
            <tr>
                <td style="width:100%" colspan="4">
                    <span>Place:<u>{56}</u></span>
                    <span>Signature:<u>{57}</u></span>
                </td>
            </tr>
            <tr>
                <td style="width:100%" colspan="4">
                    <span>Date:<u>{58}</u></span>
                    <span>Time:<u>{59}</u></span>
                </td>
            </tr>
            <tr>
                <td colspan="4"><span><strong>* IF ANY BOX IS CHECKED “NO”, DO NOT ACCEPT THE SHIPMENT AND GIVE
                    A DUPLICATE COPY OF THIS COMPLETED FORM TO THE SHIPPER.</strong></span></td>
            </tr>
            <tr>
                <td colspan="4"><span>{60}st EDITION, 1 JANUARY {61}</span></td>
            </tr>
        </table>
    </body>
</html>
"""
options = {
        'dpi': 10000
    }
config_img = imgkit.config(wkhtmltoimage="D:\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
imgkit.from_string(test_html, pdf_path + "pdf-" + pdf_uuid + ".pdf", config=config_img, options=options)