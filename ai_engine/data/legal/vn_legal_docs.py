"""
Dữ liệu pháp lý Việt Nam — tóm tắt các NĐ/Luật quan trọng cho startup.
Mỗi document gồm:
  - id: mã duy nhất
  - text: nội dung tóm tắt (chunk ~500 tokens)
  - metadata: {source, article_number, penalty_amount, industry_tags, doc_type, year}

Dữ liệu này dùng để index vào ChromaDB → Legal Agent tra cứu qua RAG.
Trong production (bản thương mại): thay bằng full text từ VBPL chính thức.
"""

LEGAL_DOCUMENTS = [
    # ══════════════════════════════════════════════════════════════
    # NĐ 15/2018/NĐ-CP — An toàn thực phẩm (ATTP)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "nd15-2018-overview",
        "text": (
            "Nghị định 15/2018/NĐ-CP (có hiệu lực từ 02/02/2018) hướng dẫn chi tiết "
            "Luật An toàn thực phẩm 2010. Nghị định quy định điều kiện bảo đảm an toàn "
            "thực phẩm đối với sản xuất, kinh doanh thực phẩm, phụ gia thực phẩm, "
            "chất hỗ trợ chế biến thực phẩm, dụng cụ, vật liệu bao gói chứa đựng thực phẩm. "
            "Thay thế NĐ 38/2012 với nhiều cải cách: bãi bỏ quy định phải có Giấy xác nhận "
            "kiến thức ATTP cho cá nhân; tự công bố sản phẩm thay vì xin giấy phép; "
            "giảm thủ tục hành chính cho doanh nghiệp nhỏ."
        ),
        "metadata": {
            "source": "NĐ 15/2018/NĐ-CP",
            "article_number": "Toàn văn",
            "penalty_amount": "",
            "industry_tags": "F&B,thực phẩm,đồ uống,nhà hàng,quán ăn,cafe,trà sữa",
            "doc_type": "Nghị định",
            "year": "2018",
        },
    },
    {
        "id": "nd15-2018-tu-cong-bo",
        "text": (
            "Theo NĐ 15/2018, Điều 4-8: Cơ sở sản xuất/kinh doanh thực phẩm được TỰ CÔNG BỐ "
            "sản phẩm (thay vì phải xin giấy phép). Hồ sơ tự công bố gồm: bản tự công bố, "
            "phiếu kết quả kiểm nghiệm sản phẩm trong vòng 12 tháng. Sản phẩm tự công bố "
            "được lưu thông ngay sau khi nộp hồ sơ. Cơ sở kinh doanh dịch vụ ăn uống "
            "(nhà hàng, quán ăn, quán cafe, trà sữa) phải đảm bảo: nguồn nước đạt chuẩn, "
            "có trang thiết bị bảo quản thực phẩm, người trực tiếp chế biến phải khám sức khỏe "
            "định kỳ, có giấy chứng nhận đủ điều kiện ATTP từ cơ quan có thẩm quyền."
        ),
        "metadata": {
            "source": "NĐ 15/2018/NĐ-CP",
            "article_number": "Điều 4-8",
            "penalty_amount": "",
            "industry_tags": "F&B,thực phẩm,đồ uống,nhà hàng,quán ăn,cafe,trà sữa",
            "doc_type": "Nghị định",
            "year": "2018",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # NĐ 115/2018/NĐ-CP — Xử phạt vi phạm ATTP
    # ══════════════════════════════════════════════════════════════
    {
        "id": "nd115-2018-phat",
        "text": (
            "Nghị định 115/2018/NĐ-CP quy định xử phạt vi phạm hành chính về an toàn thực phẩm. "
            "Mức phạt chính: "
            "- Kinh doanh thực phẩm không đảm bảo ATTP: phạt 1-3 triệu đồng (cá nhân), "
            "2-6 triệu (tổ chức). "
            "- Không có Giấy chứng nhận cơ sở đủ điều kiện ATTP: phạt 20-30 triệu đồng. "
            "- Sử dụng nguyên liệu không rõ nguồn gốc: phạt 10-20 triệu đồng. "
            "- Sử dụng phụ gia thực phẩm cấm: phạt 30-50 triệu đồng. "
            "- Vi phạm nghiêm trọng: đình chỉ hoạt động 1-3 tháng, tước giấy phép, "
            "truy cứu trách nhiệm hình sự nếu gây hậu quả nghiêm trọng. "
            "Thẩm quyền xử phạt: UBND cấp xã/huyện/tỉnh, Thanh tra chuyên ngành, Công an."
        ),
        "metadata": {
            "source": "NĐ 115/2018/NĐ-CP",
            "article_number": "Điều 2-25",
            "penalty_amount": "1-50 triệu, đình chỉ 1-3 tháng",
            "industry_tags": "F&B,thực phẩm,đồ uống,nhà hàng,quán ăn,cafe,trà sữa",
            "doc_type": "Nghị định xử phạt",
            "year": "2018",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # NĐ 106/2025/NĐ-CP — PCCC (Phòng cháy chữa cháy)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "nd106-2025-pccc",
        "text": (
            "Nghị định 106/2025/NĐ-CP quy định chi tiết về phòng cháy chữa cháy (PCCC) "
            "và cứu nạn cứu hộ. Các cơ sở kinh doanh PHẢI có: "
            "- Giấy chứng nhận thẩm duyệt thiết kế về PCCC (đối với công trình thuộc danh mục). "
            "- Phương án chữa cháy được cơ quan Công an phê duyệt. "
            "- Hệ thống báo cháy, chữa cháy (bình chữa cháy, vòi nước, đèn EXIT). "
            "- Lối thoát hiểm đạt chuẩn (không bị chặn, có biển chỉ dẫn). "
            "- Huấn luyện PCCC cho nhân viên (ít nhất 1 lần/năm). "
            "Mức phạt vi phạm PCCC: 15-25 triệu (cá nhân), 30-50 triệu (tổ chức). "
            "Vi phạm nghiêm trọng: đình chỉ hoạt động, truy cứu hình sự. "
            "Đặc biệt quan trọng với: nhà hàng, quán bar, karaoke, khách sạn, trung tâm thương mại, "
            "cơ sở sản xuất, kho bãi."
        ),
        "metadata": {
            "source": "NĐ 106/2025/NĐ-CP",
            "article_number": "Toàn văn",
            "penalty_amount": "15-50 triệu, đình chỉ hoạt động",
            "industry_tags": "F&B,nhà hàng,quán bar,karaoke,khách sạn,sản xuất,kho bãi,bán lẻ,retail",
            "doc_type": "Nghị định",
            "year": "2025",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # NĐ 122/2021/NĐ-CP — Kinh doanh không giấy phép
    # ══════════════════════════════════════════════════════════════
    {
        "id": "nd122-2021-khong-giay-phep",
        "text": (
            "Nghị định 122/2021/NĐ-CP quy định xử phạt vi phạm hành chính trong lĩnh vực "
            "kế hoạch và đầu tư. Mức phạt kinh doanh không đăng ký: "
            "- Kinh doanh không đăng ký hộ kinh doanh: phạt 5-10 triệu đồng. "
            "- Kinh doanh không đăng ký doanh nghiệp khi thuộc diện phải đăng ký: "
            "phạt 10-20 triệu đồng. "
            "- Kinh doanh ngành nghề CÓ ĐIỀU KIỆN mà không đáp ứng điều kiện: "
            "phạt 20-30 triệu đồng. "
            "- Hoạt động kinh doanh khi đã bị thu hồi giấy phép: phạt 30-50 triệu đồng. "
            "Biện pháp bổ sung: buộc đăng ký kinh doanh, đình chỉ hoạt động, "
            "tịch thu tang vật vi phạm."
        ),
        "metadata": {
            "source": "NĐ 122/2021/NĐ-CP",
            "article_number": "Điều 46-55",
            "penalty_amount": "5-50 triệu, đình chỉ hoạt động",
            "industry_tags": "tất cả,startup,doanh nghiệp,hộ kinh doanh",
            "doc_type": "Nghị định xử phạt",
            "year": "2021",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # Luật Doanh nghiệp 2020 (Luật số 59/2020/QH14)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "luat-dn-2020-loai-hinh",
        "text": (
            "Luật Doanh nghiệp 2020 (Luật số 59/2020/QH14, có hiệu lực từ 01/01/2021) "
            "quy định 5 loại hình doanh nghiệp: "
            "1. Doanh nghiệp tư nhân (DNTN): 1 chủ, chịu trách nhiệm bằng toàn bộ tài sản, "
            "không được phát hành chứng khoán. "
            "2. Công ty TNHH 1 thành viên: 1 chủ sở hữu (cá nhân/tổ chức), vốn điều lệ tự khai, "
            "chịu trách nhiệm trong phạm vi vốn góp. "
            "3. Công ty TNHH 2+ thành viên: 2-50 thành viên, không được phát hành cổ phiếu. "
            "4. Công ty cổ phần (CTCP): từ 3 cổ đông trở lên, được phát hành cổ phiếu, "
            "phù hợp khi muốn gọi vốn đầu tư. "
            "5. Công ty hợp danh: ít nhất 2 thành viên hợp danh, chịu trách nhiệm vô hạn. "
            "Khuyến nghị cho startup: TNHH 1TV (solo founder) hoặc CTCP (nếu có co-founder, "
            "hoặc dự kiến gọi vốn). Thời gian đăng ký: 3-5 ngày làm việc qua mạng."
        ),
        "metadata": {
            "source": "Luật Doanh nghiệp 2020 (59/2020/QH14)",
            "article_number": "Điều 74-177",
            "penalty_amount": "",
            "industry_tags": "tất cả,startup,doanh nghiệp,đăng ký kinh doanh",
            "doc_type": "Luật",
            "year": "2020",
        },
    },
    {
        "id": "luat-dn-2020-nganh-dieu-kien",
        "text": (
            "Luật Doanh nghiệp 2020, Điều 7: Ngành nghề kinh doanh có điều kiện. "
            "Danh mục ngành nghề đầu tư kinh doanh có điều kiện theo Phụ lục IV Luật Đầu tư 2020 "
            "(Luật 61/2020/QH14), gồm 227 ngành nghề. Ví dụ: "
            "- Kinh doanh dịch vụ ăn uống (F&B): cần Giấy chứng nhận đủ điều kiện ATTP. "
            "- Kinh doanh dược phẩm: cần Giấy chứng nhận đủ điều kiện kinh doanh dược. "
            "- Kinh doanh bất động sản: vốn pháp định 20 tỷ đồng. "
            "- Dịch vụ tài chính: cần giấy phép từ NHNN hoặc BTC. "
            "- Giáo dục: cần giấy phép từ Sở GD&ĐT. "
            "- Edtech/Fintech: có thể chịu quy định sandbox (thử nghiệm có giám sát)."
        ),
        "metadata": {
            "source": "Luật Doanh nghiệp 2020 + Luật Đầu tư 2020",
            "article_number": "Điều 7, Phụ lục IV",
            "penalty_amount": "",
            "industry_tags": "tất cả,F&B,dược,bất động sản,tài chính,giáo dục,edtech,fintech",
            "doc_type": "Luật",
            "year": "2020",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # Luật Sở hữu trí tuệ 2022 (sửa đổi)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "luat-shtt-2022",
        "text": (
            "Luật Sở hữu trí tuệ 2022 (sửa đổi Luật SHTT 2005, có hiệu lực từ 01/01/2023). "
            "Startup cần lưu ý: "
            "- Đăng ký nhãn hiệu (trademark): nộp đơn tại Cục SHTT, phí ~1-3 triệu, "
            "thời gian xử lý 12-18 tháng. NÊN đăng ký sớm trước khi launch. "
            "- Bản quyền (copyright): tự động phát sinh, không bắt buộc đăng ký nhưng nên đăng ký "
            "để dễ bảo vệ quyền. Đặc biệt quan trọng với phần mềm, nội dung sáng tạo. "
            "- Sáng chế (patent): yêu cầu tính mới, trình độ sáng tạo, khả năng áp dụng CN. "
            "Thời gian bảo hộ 20 năm. Chi phí đăng ký ~10-30 triệu. "
            "- Vi phạm SHTT: phạt 5-250 triệu tùy mức độ, buộc bồi thường thiệt hại. "
            "- Startup công nghệ: code nguồn được bảo hộ quyền tác giả; thuật toán AI "
            "có thể đăng ký sáng chế nếu đáp ứng tiêu chí."
        ),
        "metadata": {
            "source": "Luật SHTT 2022 (sửa đổi)",
            "article_number": "Toàn văn",
            "penalty_amount": "5-250 triệu",
            "industry_tags": "tất cả,startup,công nghệ,tech,phần mềm,AI,sáng tạo",
            "doc_type": "Luật",
            "year": "2022",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # Luật AI 134/2025/QH15 — Trí tuệ nhân tạo
    # ══════════════════════════════════════════════════════════════
    {
        "id": "luat-ai-2025-overview",
        "text": (
            "Luật Trí tuệ nhân tạo (Luật số 134/2025/QH15, có hiệu lực từ 01/01/2026). "
            "Đây là luật AI ĐẦU TIÊN của Việt Nam, quy định: "
            "- Phân loại hệ thống AI theo mức rủi ro: Rủi ro không chấp nhận được (cấm), "
            "Rủi ro cao (quản lý chặt), Rủi ro hạn chế (minh bạch), Rủi ro tối thiểu (tự do). "
            "- Hệ thống AI rủi ro cao: y tế, tài chính, tuyển dụng, chấm điểm tín dụng, "
            "giám sát an ninh → PHẢI đăng ký + đánh giá tác động trước khi triển khai. "
            "- Minh bạch: sản phẩm/dịch vụ dùng AI PHẢI thông báo cho người dùng biết "
            "rằng họ đang tương tác với AI. "
            "- Bảo vệ dữ liệu: hệ thống AI phải tuân thủ Luật An ninh mạng VN + "
            "NĐ về bảo vệ dữ liệu cá nhân. "
            "- Trách nhiệm: tổ chức triển khai AI chịu trách nhiệm về thiệt hại do AI gây ra. "
            "- Sandbox: Chính phủ có thể cho phép thử nghiệm AI trong môi trường sandbox "
            "có giám sát trước khi triển khai chính thức."
        ),
        "metadata": {
            "source": "Luật AI 134/2025/QH15",
            "article_number": "Toàn văn",
            "penalty_amount": "Chưa ban hành NĐ hướng dẫn xử phạt",
            "industry_tags": "AI,tech,công nghệ,phần mềm,y tế,tài chính,fintech,edtech",
            "doc_type": "Luật",
            "year": "2025",
        },
    },
    {
        "id": "luat-ai-2025-startup",
        "text": (
            "Luật AI 134/2025/QH15 — Tác động đến startup AI tại Việt Nam: "
            "1. Chatbot/AI advisor: thuộc nhóm 'rủi ro hạn chế' → PHẢI ghi rõ 'Đây là AI, "
            "không phải con người' trên giao diện. "
            "2. AI trong y tế/tài chính: thuộc nhóm 'rủi ro cao' → cần đăng ký, đánh giá tác động, "
            "kiểm toán thuật toán (algorithm audit). "
            "3. Deepfake/Social scoring: thuộc nhóm 'cấm' → KHÔNG được triển khai. "
            "4. Thu thập dữ liệu training: phải tuân thủ Luật An ninh mạng 2018 + "
            "NĐ 13/2023 về bảo vệ dữ liệu cá nhân → xin đồng ý (consent) người dùng, "
            "lưu trữ dữ liệu trong lãnh thổ VN (nếu dữ liệu quan trọng). "
            "5. Startup AI nên: "
            "- Đăng ký sandbox nếu sản phẩm thuộc lĩnh vực quản lý chặt. "
            "- Có chính sách Responsible AI (AI có trách nhiệm). "
            "- Thuê tư vấn pháp lý chuyên AI compliance trước khi launch."
        ),
        "metadata": {
            "source": "Luật AI 134/2025/QH15",
            "article_number": "Điều 8-15",
            "penalty_amount": "Chưa ban hành NĐ xử phạt cụ thể",
            "industry_tags": "AI,tech,chatbot,y tế,tài chính,deepfake,startup",
            "doc_type": "Luật",
            "year": "2025",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # Luật An ninh mạng 2018 + NĐ 13/2023 (Bảo vệ dữ liệu cá nhân)
    # ══════════════════════════════════════════════════════════════
    {
        "id": "luat-anm-2018-data",
        "text": (
            "Luật An ninh mạng 2018 (Luật 24/2018/QH14) + NĐ 13/2023/NĐ-CP về bảo vệ dữ liệu "
            "cá nhân. Startup cần lưu ý: "
            "- Thu thập dữ liệu cá nhân PHẢI được đồng ý (consent) của chủ thể dữ liệu. "
            "- Dữ liệu cá nhân nhạy cảm (sức khỏe, tài chính, sinh trắc học): "
            "cần đánh giá tác động trước khi xử lý. "
            "- Lưu trữ dữ liệu: doanh nghiệp VN xử lý dữ liệu người dùng VN "
            "phải lưu trữ dữ liệu tại VN (localization). "
            "- Thông báo vi phạm: nếu bị rò rỉ dữ liệu, phải thông báo Bộ Công an + "
            "chủ thể dữ liệu trong 72 giờ. "
            "- Mức phạt: vi phạm bảo vệ dữ liệu cá nhân phạt 50-100 triệu (cá nhân), "
            "100-200 triệu (tổ chức). "
            "- Đặc biệt quan trọng với: app có đăng ký tài khoản, ecommerce, fintech, "
            "healthtech, edtech, mạng xã hội."
        ),
        "metadata": {
            "source": "Luật An ninh mạng 2018 + NĐ 13/2023/NĐ-CP",
            "article_number": "Toàn văn",
            "penalty_amount": "50-200 triệu",
            "industry_tags": "tất cả,tech,app,ecommerce,fintech,healthtech,edtech,mạng xã hội,AI",
            "doc_type": "Luật + Nghị định",
            "year": "2018,2023",
        },
    },

    # ══════════════════════════════════════════════════════════════
    # Thuế — Quy định cơ bản cho startup
    # ══════════════════════════════════════════════════════════════
    {
        "id": "thue-startup-2024",
        "text": (
            "Quy định thuế cơ bản cho startup Việt Nam (cập nhật 2024-2025): "
            "1. Thuế TNDN (thu nhập doanh nghiệp): "
            "- Thuế suất phổ thông: 20%. "
            "- Doanh nghiệp nhỏ (doanh thu < 10 tỷ/năm): 15-17% (đề xuất). "
            "- Ưu đãi thuế: DN công nghệ cao, startup trong khu CNC → thuế 10% trong 15 năm. "
            "2. Thuế VAT (giá trị gia tăng): "
            "- Thuế suất phổ thông: 10% (8% giai đoạn giảm thuế). "
            "- Dịch vụ giáo dục, y tế: 5% hoặc miễn. "
            "- Xuất khẩu phần mềm: 0%. "
            "3. Thuế TNCN (thu nhập cá nhân): "
            "- Lương nhân viên: thuế lũy tiến 5-35% (khấu trừ giảm trừ gia cảnh 11 triệu/tháng). "
            "4. Hóa đơn điện tử: BẮT BUỘC từ 01/07/2022. Mọi giao dịch phải xuất hóa đơn điện tử."
        ),
        "metadata": {
            "source": "Luật Thuế TNDN, Luật Thuế VAT, Luật Thuế TNCN",
            "article_number": "Tổng hợp",
            "penalty_amount": "",
            "industry_tags": "tất cả,startup,doanh nghiệp,thuế",
            "doc_type": "Tổng hợp thuế",
            "year": "2024",
        },
    },
]
