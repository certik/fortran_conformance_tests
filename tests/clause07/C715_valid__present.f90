! rule: C715
! covers: present-first
! evidence: positive-control
program c715_present
    implicit none
    integer :: actual = 7
    integer :: seen = -1
    call probe(seen, actual)
    if (seen /= 1) error stop 'present'
    seen = -1
    call probe(seen)
    if (seen /= 0) error stop 'absent'
contains
    subroutine probe(observed, x)
        integer, intent(out) :: observed
        type(*), optional, intent(in) :: x
        observed = 0
        if (present(x)) observed = 1
    end subroutine
end program
