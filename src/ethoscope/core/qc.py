from PIL import ImageStat


class QualityControl:

    def __init__(self, result_writer):

        self.result_writer = result_writer

        result_writer._create_table(
            "QC", "t INT, \
            mean_red FLOAT, mean_green FLOAT, mean_blue FLOAT, \
            min_red FLOAT, max_red FLOAT, \
            min_green FLOAT, max_green FLOAT, \
            min_blue FLOAT, max_blue FLOAT"
            )

    @staticmethod
    def image_stat(frame):
        current_image = Image.open(frame)
        logging.warning(current_image)
        current_image.convert()
        logging.warning(current_image)
        return ImageStat.Stat(current_image)

    def qc(self, frame):
        stat = self.image_stat(frame)
        return {"stat": stat}




    def write(self, t, qc):
        command = "INSERT INTO \
        QC (t, mean_read, mean_green, mean_blue, min_red, max_red, min_green, max_gren, min_blue, max_blue) \
        VALUES ({t}, {qc['stat'].mean[0]}, {qc['stat'].mean[1]}, {qc['stat'].mean[2]}, \
            {qc['stat'].extrema[0][0]}, {qc['stat'].extrema[0][1]}, {qc['stat'].extrema[1][0]}, \
            {qc['stat'].extrema[1][1]}, {qc['stat'].extrema[2][0]}, {qc['stat'].extrema[0][1]})"

        if "QC" not in self.result_writer._insert_dict or self.result_writer._insert_dict == "":
            self.result_writer._insert_dict["QC"] = command
        else:
            self.result_writer._insert_dict["QC"] += command

