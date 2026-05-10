from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from controllers.certificate_controller import CertificateController
from services.interfaces.certificate_service import CertificateDTO
from ui.widgets.table_utils import apply_table_column_resize, configure_table, set_row_height, set_table_buttons, table_button


class MyCertificateView(QWidget):
    def __init__(self, certificate_controller: CertificateController) -> None:
        super().__init__()
        self._certificate_controller = certificate_controller

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("我的证书")
        title.setObjectName("pageTitle")

        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("primaryButton")
        refresh_button.clicked.connect(self.refresh)

        self._empty_label = QLabel("暂无证书")
        self._empty_label.setObjectName("placeholderHint")

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["活动名称", "证书编号", "生成时间", "文件路径", "操作"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        configure_table(self._table)

        layout.addWidget(title)
        layout.addWidget(refresh_button)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)

        self.refresh()

    def refresh(self) -> None:
        result = self._certificate_controller.list_my_certificates()
        if not result.success:
            QMessageBox.warning(self, "查询失败", result.message)
            return
        self._render(result.certificates or [])

    def _render(self, certificates: list[CertificateDTO]) -> None:
        self._table.setRowCount(len(certificates))
        self._empty_label.setVisible(len(certificates) == 0)
        self._table.setVisible(len(certificates) > 0)

        for row, certificate in enumerate(certificates):
            set_row_height(self._table, row)
            values = [
                certificate.activity_title,
                certificate.certificate_no,
                certificate.generated_at.strftime("%Y-%m-%d %H:%M"),
                str(certificate.file_path),
            ]
            for column, value in enumerate(values):
                self._table.setItem(row, column, QTableWidgetItem(value))

            open_button = table_button(
                "打开证书",
                lambda file_path=certificate.file_path: self._open_certificate(file_path),
            )
            set_table_buttons(self._table, row, 4, open_button)
        apply_table_column_resize(self._table)

    def _open_certificate(self, file_path) -> None:
        if not file_path.exists():
            QMessageBox.warning(self, "打开失败", "证书文件不存在。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
