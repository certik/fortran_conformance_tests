module calibration_api
    use iso_c_binding, only: c_int
    implicit none
    interface
        function c_scale(n, values) bind(c, name="calibration_scale") result(total)
            import c_int
            integer(c_int), value :: n
            integer(c_int), intent(inout) :: values(*)
            integer(c_int) :: total
        end function
    end interface
contains
    function roundtrip(values) result(total)
        integer(c_int), intent(inout) :: values(:)
        integer(c_int) :: total
        total = c_scale(size(values, kind=c_int), values)
    end function
end module
