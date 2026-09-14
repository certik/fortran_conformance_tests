! rule: R403
! covers: logical-literal-control logical-variable-control
! evidence: positive-control
program scalar_alias
    implicit none
    integer :: result
    logical :: choose
    result = 0
    if (.true.) result = 1
    choose = .true.
    if (choose) result = result + 2
    if (result /= 3) stop 1
end program scalar_alias
