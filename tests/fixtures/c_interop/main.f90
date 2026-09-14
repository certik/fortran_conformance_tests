program calibration_interop
    use iso_c_binding, only: c_int
    use calibration_api, only: roundtrip
    implicit none
    integer(c_int) :: values(3), total
    values = [2_c_int, 3_c_int, 5_c_int]
    total = roundtrip(values)
    if (total /= 20) error stop 'C result'
    if (any(values /= [4, 6, 10])) error stop 'C pointer argument'
    write(*, '(a,ss,i0)') 'BRIDGE=', total
end program
