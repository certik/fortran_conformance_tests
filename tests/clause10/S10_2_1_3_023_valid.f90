! rule: S10.2.1.3-023
! covers: same-image-control
! evidence: context-only
! F2023 10.2.1.3 p14: these controls do not establish the undefined cross-image result.
module s10_2_1_3_023_m
    use iso_c_binding, only: c_int
    implicit none
contains
    integer(c_int) function add_one(x) bind(c)
        integer(c_int), value :: x
        add_one = x + 1
    end function
end module
program s10_2_1_3_023_valid
    use iso_c_binding, only: c_int, c_ptr, c_funptr, c_loc, c_funloc, c_associated, c_f_pointer
    use s10_2_1_3_023_m
    implicit none
    integer(c_int), target :: value
    integer(c_int), pointer :: pointed
    type(c_ptr) :: source, copy
    type(c_funptr) :: procedure_source, procedure_copy
    value = 17
    source = c_loc(value)
    copy = source
    if (.not. c_associated(copy, source)) error stop 'same-image-c-ptr'
    call c_f_pointer(copy, pointed)
    if (.not. associated(pointed)) error stop 'same-image-target-association'
    if (pointed /= 17) error stop 'same-image-target-value'
    procedure_source = c_funloc(add_one)
    procedure_copy = procedure_source
    if (.not. c_associated(procedure_copy, procedure_source)) error stop 'same-image-c-funptr'
end program
