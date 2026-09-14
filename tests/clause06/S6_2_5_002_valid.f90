! rule: S6.2.5-002
! covers: distinct-labels independent-scopes
! evidence: positive-control
program label_scopes
    implicit none
    integer :: value
    value = 0
10  continue
20  call inside(value)
30  call outside(value)
    if (value /= 2) error stop 1
contains
    subroutine inside(value)
        integer, intent(inout) :: value
10      continue
        value = value + 1
    end subroutine
end program

subroutine outside(value)
    implicit none
    integer, intent(inout) :: value
10  continue
    value = value + 1
end subroutine
