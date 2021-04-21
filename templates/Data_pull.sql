SELECT * 
FROM [dbo].[HOUSEHOLDS] JOIN [dbo].[TRANSACTIONS] ON [dbo].[TRANSACTIONS].[HSHD_NUM] = [dbo].[HOUSEHOLDS].[HSHD_NUM] 
                        JOIN [dbo].[PRODUCTS] ON [dbo].[TRANSACTIONS].[PRODUCT_NUM] = [dbo].[PRODUCTS].[PRODUCT_NUM]
                        WHERE [dbo].[HOUSEHOLDS].HSHD_NUM = 10;