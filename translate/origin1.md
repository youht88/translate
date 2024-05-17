[![Alipay, China's leading third-party online payment solution](https://ac.alipay.com/storage/2024/3/26/d66c43c0-440d-4c97-9976-f2028a2c8c5e.svg)![Alipay, China's leading third-party online payment solution](https://ac.alipay.com/storage/2024/3/26/a48bd336-aea0-4f16-bf83-616eacbb4434.svg)](/docs/)

[Go to Homepage](../../)

Scan to Bind

[Overview](/docs/ac/scantopay_en/overview)

Integration guide

After payments

[Reconciliation](/docs/ac/scantopay_en/settle_reconcile)

Overview
========

2023-08-31 08:16

[中文版](https://global.alipay.com/docs/ac/scantopay_cn/overview)

Scan to Bind enables buyers to conveniently authorize payments on devices such as PCs, game consoles, and smart TVs by scanning the authorization code with their mobile phones. After authorization, subsequent payments can be completed with just one click. Buyers can directly scan the QR code on your page to authorize payments, eliminating the need to be redirected to the payment method page, thereby increasing payment success rates.

Key features
============

Scan to Bind boasts the following product highlights:

*   **Minimalist payment experience**: Enhance payment conversion rates by enabling one-click subsequent payments for buyers through successful payment authorization on their mobile phones.
*   **Local payment methods**: Provide local buyers with trusted and familiar payment methods to maximize authorization success rates.
*   **Light-weight Integration**: Integrate only once to enjoy the latest payment methods and payment experiences without incurring additional development costs, enabling you to rapidly expand into new markets.

User experience
===============

Buyers authorize payments by scanning the authorization code on their mobile phones. For subsequent payments, buyers only need to click once on your client to complete the payment.

Scenario 1: First-time payment
------------------------------

Buyers scan the code to authorize payments, thus enabling subsequent payments without verification for this payment method.  

![image](https://ac.alipay.com/storage/2020/5/11/793a3d8d-5270-405b-9362-e6a670b9c842.png "image")

Scenario 2: Subsequent payments
-------------------------------

Buyers select the authorized payment method for a subsequent payment and complete the payment directly with one click.

![扫码签约钱包后续支付.png](https://ac.alipay.com/storage/2020/5/11/793a3d8d-5270-405b-9362-e6a670b9c842.png "扫码签约钱包后续支付.png")

Capabilities and resources
--------------------------

*   To integrate the Scan to Bind service, see [Obtain authorization](https://global.alipay.com/docs/ac/scan_to_bind_en/authorization)
     to obtain a buyer's authorization, and see [Pay](https://global.alipay.com/docs/ac/scan_to_bind_en/pay)
     to initiate a payment after you have obtained the buyer's authorization.
*   For information about the operations after the payment, see [Refund](https://global.alipay.com/docs/ac/scan_to_bind_en/refund)
    , [Cancel](https://global.alipay.com/docs/ac/scan_to_bind_en/cancel)
    , and [Notifications](https://global.alipay.com/docs/ac/scan_to_bind_en/notification)
    .
*   The following table lists all the APIs, notifications, and reports for Scan to Bind, serving the purpose of facilitating the payment and after-the-payment processes:

|     |     |     |
| --- | --- | --- |
| **Capabilities** | **Development resources** |     |
| **Server APIs** | **Server** **Notifications/Reports** |
| **Obtain authorization** | [consult](https://global.alipay.com/docs/ac/ams/authconsult) | [notifyAuthorization](https://global.alipay.com/docs/ac/ams/notifyauth) |
| **Revoke authorization** | [revoke](https://global.alipay.com/docs/ac/ams/authrevocation) | [notifyAuthorization](https://global.alipay.com/docs/ac/ams/notifyauth) |
| **Apply for a payment token** | [applyToken](https://global.alipay.com/docs/ac/ams/accesstokenapp) |     |
| **Initiate a payment** | [pay (Auto Debit)](https://global.alipay.com/docs/ac/ams/payment_agreement)<br><br>[inquiryPayment](https://global.alipay.com/docs/ac/ams/paymentri_online) | [inquiryPayment](https://global.alipay.com/docs/ac/ams/paymentrn_online) |
| **Cancel a payment** | [cancel](https://global.alipay.com/docs/ac/ams/paymentc_online) |     |
| **Refund a payment** | [refund](https://global.alipay.com/docs/ac/ams/refund_online)<br><br>[inquiryRefund](https://global.alipay.com/docs/ac/ams/ir_online) | [notifyRefund](https://global.alipay.com/docs/ac/ams/notify_refund) |
| **Declare goods** | [declare](https://global.alipay.com/docs/ac/ams/declare)<br><br>[inquiryDeclarationRequests](https://global.alipay.com/docs/ac/ams/inquirydeclare) |     |
| **Settle and reconcile** |     | [Transaction details](https://global.alipay.com/docs/ac/reconcile/transaction_details)<br><br>[Settlement details](https://global.alipay.com/docs/ac/reconcile/settlement_details)<br><br>[Settlement summary](https://global.alipay.com/docs/ac/reconcile/settlement_summary) |

Table 1. APIs, notifications, and reports used for Scan to bind

Supported payment methods
=========================

The following payment methods are supported for Scan to bind. Their capabilities are listed as follows:

|     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Payment method** | **Buyer country/region** | **Supported currency** | **Refund** | **Partial refund** | **Chargeback** | **Minimum payment amount** | **Maximum payment amount** | **Refund period** |
| AlipayHK | Hong Kong, China | HKD | ✔️  | ✔️  | ❌   | 0.01 HKD per transaction | 50,000 HKD per transaction；  <br>200,000 HDK per year | 365 days |
| DANA | Indonesia | IDR | ✔️  | ✔️  | ❌   | 300 IDR | 10,000,000 IDR per transaction; 20,000,000 IDR per day | 365 days |

Table 2. Supported payment methods

![](https://ac.alipay.com/storage/2021/5/20/19b2c126-9442-4f16-8f20-e539b1db482a.png)![](https://ac.alipay.com/storage/2021/5/20/e9f3f154-dbf0-455f-89f0-b3d4e0c14481.png)

@2024 Alipay [Legal Information](https://global.alipay.com/docs/ac/platform/membership)
 

#### On this page

[Key features](#uugdl "Key features")

[User experience](#2lQCL "User experience")

[Scenario 1: First-time payment](#4LBDz "Scenario 1: First-time payment")

[Scenario 2: Subsequent payments](#elK1T "Scenario 2: Subsequent payments")

[Capabilities and resources](#rcMbR "Capabilities and resources")

[Supported payment methods](#xGPEk "Supported payment methods")