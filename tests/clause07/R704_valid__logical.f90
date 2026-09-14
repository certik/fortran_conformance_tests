! rule: R704
! covers: logical-default logical-selector
! evidence: positive-control
program p
    implicit none
    logical :: a = .true.
    logical(kind=kind(.true.)) :: b = .false.
    if (.not. a) error stop 1
    if (b) error stop 2
end program
