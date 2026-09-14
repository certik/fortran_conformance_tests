program default_c_descriptor_mappings
    use iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_char
    implicit none
    integer, parameter :: real_mappings(3) = [c_float, c_double, c_long_double]
    if (c_int < 0) error stop 'required-c-int-unavailable'
    if (c_char < 0 .or. c_char /= kind('a')) stop 77
    if (.not. any(real_mappings >= 0 .and. real_mappings == kind(0.0))) stop 77
    if (.not. any(real_mappings >= 0 .and. real_mappings == kind(0.0d0))) stop 77
end program
