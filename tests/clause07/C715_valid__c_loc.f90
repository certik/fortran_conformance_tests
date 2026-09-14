! rule: C715
! covers: c-loc-first
! evidence: positive-control
program c715_c_loc
    use iso_c_binding, only: c_int, c_ptr, c_null_ptr, c_loc, c_associated
    implicit none
    integer(c_int), target :: actual = 43_c_int
    type(c_ptr) :: expected = c_null_ptr
    logical :: seen = .false.
    expected = c_loc(actual)
    if (.not. c_associated(expected)) error stop 'actual-address'
    call probe(actual, expected, seen)
    if (.not. seen) error stop 'same-address'
    if (actual /= 43_c_int) error stop 'unchanged-actual'
contains
    subroutine probe(x, address, observed)
        type(*), target, intent(in) :: x
        type(c_ptr), intent(in) :: address
        logical, intent(out) :: observed
        type(c_ptr) :: received
        received = c_null_ptr
        received = c_loc(x)
        if (.not. c_associated(received)) error stop 'dummy-address'
        observed = c_associated(received, address)
    end subroutine
end program
