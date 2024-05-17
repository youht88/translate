[![支付宝——中国领先的第三方在线支付解决方案](https://ac.alipay.com/storage/2024/3/26/d66c43c0-440d-4c97-9976-f2028a2c8c5e.svg)![支付宝——中国领先的第三方在线支付解决方案](https://ac.alipay.com/storage/2024/3/26/a48bd336-aea0-4f16-bf83-616eacbb4434.svg)](/docs/zh-CN/)

[回到首页](../../)

扫一扫绑定

[概述](/docs/zh-CN/ac/scantopay/overview)

集成指南

付款后

[对账](/docs/zh-CN/ac/scantopay/settle_reconcile)

概述
-----

2023-08-31 08:16

[中文版](https://global.alipay.com/docs/ac/scantopay/overview)

扫一扫绑定允许买家通过在手机上扫描授权码，便捷地在PC、游戏机、智能电视等设备上授权支付。授权后，后续支付只需一次点击即可完成。买家可以直接扫描页面上的二维码进行支付授权，无需跳转到支付方式页面，从而提高支付成功率。

主要特点
---------

扫一扫绑定具有以下产品亮点：

*   **简洁的支付体验**：通过手机成功授权支付，实现买家一键式后续支付，提升支付转化率。
*   **本地支付方式**：为本地买家提供信任且熟悉的支付方式，以最大化授权成功率。
*   **轻量级集成**：一次性集成，享受最新的支付方式和支付体验，无需额外的开发成本，快速拓展新市场。

用户体验
---------

买家通过手机扫描授权码进行支付授权。对于后续支付，买家只需在您的客户端上点击一次即可完成支付。

场景1：首次支付
-----------------

买家扫描代码授权支付，为此支付方式启用后续支付，无需验证。

![image](https://ac.alipay.com/storage/2020/5/11/793a3d8d-5270-405b-9362-e6a670b9c842.png "image")

场景2：后续支付
----------------

买家选择已授权的支付方式，一键完成后续支付。

![扫码签约钱包后续支付.png](https://ac.alipay.com/storage/2020/5/11/793a3d8d-5270-405b-9362-e6a670b9c842.png "扫码签约钱包后续支付.png")

功能与资源
-----------

*   要集成扫一扫绑定服务，请参阅[获取授权](https://global.alipay.com/docs/ac/scantopay/authorization)以获取买家授权，然后在获取授权后参阅[支付](https://global.alipay.com/docs/ac/scantopay/pay)以发起支付。
*   有关付款后操作的信息，请参阅[退款](https://global.alipay.com/docs/ac/scantopay/refund)、[取消](https://global.alipay.com/docs/ac/scantopay/cancel)和[通知](https://global.alipay.com/docs/ac/scantopay/notification)。
*   下表列出了所有适用于扫一扫绑定的API、通知和报告，以帮助处理支付和支付后流程：

|     |     |     |
| --- | --- | --- |
| **功能** | **开发资源** |     |
| **服务器API** | **服务器通知/报告** |
| **获取授权** | [咨询](https://global.alipay.com/docs/ac/ams/authconsult) | [notifyAuthorization](https://global.alipay.com/docs/ac/ams/notifyauth) |
| **撤销授权** | [撤销](https://global.alipay.com/docs/ac/ams/authrevocation) | [notifyAuthorization](https://global.alipay.com/docs/ac/ams/notifyauth) |
| **申请支付令牌** | [applyToken](https://global.alipay.com/docs/ac/ams/accesstokenapp) |     |
| **发起支付** | [支付（自动扣款）](https://global.alipay.com/docs/ac/ams/payment_agreement)<br><br>[inquiryPayment](https://global.alipay.com/docs/ac/ams/paymentri_online) | [inquiryPayment](https://global.alipay.com/docs/ac/ams/paymentrn_online) |
| **取消支付** | [cancel](https://global.alipay.com/docs/ac/ams/paymentc_online) |     |
| **退款** | [refund](https://global.alipay.com/docs/ac/ams/refund_online)<br><br>[inquiryRefund](https://global.alipay.com/docs/ac/ams/ir_online) | [notifyRefund](https://global.alipay.com/docs/ac/ams/notify_refund) |
| **申报商品** | [declare](https://global.alipay.com/docs/ac/ams/declare)<br><br>[inquiryDeclarationRequests](https://global.alipay.com/docs/ac/ams/inquirydeclare) |     |
| **结算对账** |     | [交易详情](https://global.alipay.com/docs/ac/reconcile/transaction_details)<br><br>[结算详情](https://global.alipay.com/docs/ac/reconcile/settlement_details)<br><br>[结算汇总](https://global.alipay.com/docs/ac/reconcile/settlement_summary) |

表1. 用于扫一扫绑定的API、通知和报告

支持的支付方式
----------------

扫一扫绑定支持以下支付方式，其功能如下：

|     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **支付方式** | **买家国家/地区** | **支持的货币** | **退款** | **部分退款** | **拒付** | **最低支付金额** | **最高支付金额** | **退款期** |
| AlipayHK | 中国香港 | HKD | ✔️  | ✔️  | ❌   | 每笔交易0.01 HKD | 每笔交易50,000 HKD；<br>每年200,000 HKD | 365天 |
| DANA | 印度尼西亚 | IDR | ✔️  | ✔️  | ❌   | 300 IDR | 每笔交易10,000,000 IDR；<br>每日20,000,000 IDR | 365天 |

表2. 支持的支付方式

![](https://ac.alipay.com/storage/2021/5/20/19b2c126-9442-4f16-8f20-e539b1db482a.png)![](https://ac.alipay.com/storage/2021/5/20/e9f3f154-dbf0-455f-89f0-b3d4e0c14481.png)

@2024 支付宝 [法律信息](https://global.alipay.com/docs/ac/platform/membership)

#### 本页内容

[主要特点](#uugdl "主要特点")

[用户体验](#2lQCL "用户体验")

[场景1：首次支付](#4LBDz "场景1：首次支付")

[场景2：后续支付](#elK1T "场景2：后续支付")

[功能与资源](#rcMbR "功能与资源")

[支持的支付方式](#xGPEk "支持的支付方式")