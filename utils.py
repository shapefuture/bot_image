

def get_timezone(latitude, longitude):
    import timezonefinder
    tf = timezonefinder.TimezoneFinder()
    time_zone_str = tf.timezone_at(lat=latitude, lng=longitude)
    return time_zone_str

