import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QTableView, QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QTreeView, QMessageBox, QCheckBox
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt 
import pandas as pd
from evaluation import run_instant_runoff

class DataFrameModel(QAbstractTableModel):
    def __init__(self, data=None):
        super(DataFrameModel, self).__init__()
        self.load_data(data)

    def load_data(self, data):
        self.data_frame = data if data is not None else pd.DataFrame()
        self.column_count = len(self.data_frame.columns)
        self.row_count = len(self.data_frame.index)

    def rowCount(self, parent=QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QModelIndex()):
        return self.column_count

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self.data_frame.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.data_frame.columns[section]
            else:
                return str(self.data_frame.index[section])
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Instant Runoff Voting Assessment")

        # Main layout
        main_layout = QVBoxLayout()

        # File selection and preview frame
        file_selection_layout = QHBoxLayout()
        self.file_path_entry = QtWidgets.QLineEdit(self)
        file_selection_layout.addWidget(self.file_path_entry)

        load_button = QPushButton("Load Excel", self)
        load_button.clicked.connect(self.load_excel)
        file_selection_layout.addWidget(load_button)

        main_layout.addLayout(file_selection_layout)

        # Feedback label
        self.feedback_label = QLabel("")
        main_layout.addWidget(self.feedback_label)

        # Output directory selection
        output_dir_layout = QHBoxLayout()
        self.output_dir_entry = QtWidgets.QLineEdit(self)
        output_dir_layout.addWidget(self.output_dir_entry)

        select_dir_button = QPushButton("Select Output Directory", self)
        select_dir_button.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(select_dir_button)

        main_layout.addLayout(output_dir_layout)

        # Consider invalid votes checkbox
        self.consider_invalid_var = QtWidgets.QCheckBox("Consider invalid votes (voters that have not ranked all candidates)")
        main_layout.addWidget(self.consider_invalid_var)

        # Table to preview Excel data
        self.table = QtWidgets.QTableView(self)
        main_layout.addWidget(self.table)

        # Button to run the Instant Runoff Voting process
        run_button = QPushButton("Instant-Runoff Vote Evaluation", self)
        run_button.clicked.connect(self.run_voting)
        main_layout.addWidget(run_button)

        # Set the layout for the central widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel files (*.xlsx;*.xls)")
        if file_path:
            self.file_path_entry.setText(file_path)
            
            try:
                # Attempt to read the Excel file without headers
                df = pd.read_excel(file_path, header=None)
                self.update_table(df.head())

                column_names = ['Voter-ID', 'Region1', 'Region2']
                # Check if the number of column names matches the number of columns in the DataFrame
                if len(column_names) != df.shape[1]:
                    self.feedback_label.setText("The Excel file should have exactly three columns (Voter-ID, Region 1, Region 2).")
                    return

                # Check if unique header names are included
                all_match = all(df.iloc[0, i].split('[')[0].strip() == df.iloc[1, i].split('[')[0].strip() for i in range(1, len(df.columns)))
                if not all_match:
                    self.feedback_label.setText("Please remove the header from the Excel file.")
                    return

                # If all checks pass
                self.feedback_label.setText("Excel file looks good!")
                # Additional code to process the DataFrame

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                self.feedback_label.setText("")


    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.output_dir_entry.setText(dir_path)
            # Additional code for select_output_dir

    def update_table(self, data):
        # Set the new headers for the DataFrame
        column_headers = ['Voter-ID', 'Region1', 'Region2']
        try:
            data.columns = column_headers
        except:
            pass

        # Create the model with the updated DataFrame
        model = DataFrameModel(data)
        self.table.setModel(model)
        #self.table.resizeColumnsToContents()

    def run_voting(self):
        file_path = self.file_path_entry.text()  # Get the text from QLineEdit
        output_dir = self.output_dir_entry.text()  # Get the text from QLineEdit
        consider_invalid = self.consider_invalid_var.isChecked()  # Get the check state (True/False)

        if file_path and output_dir:
            try:
                # Adjust the function to accept the output directory as an argument
                run_instant_runoff(file_path, output_dir, consider_invalid)
                QMessageBox.information(self, "Success", "Voting assessment completed. Check the output files in the specified directory.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "Please select an Excel file and output directory first.")

        # Your run_voting code here

# Your pandas DataFrame handling and other functions can be added here

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
