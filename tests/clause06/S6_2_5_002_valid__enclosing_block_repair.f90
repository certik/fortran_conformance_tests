! rule: S6.2.5-002
! covers: enclosing-block-scope
! evidence: positive-control
program label_enclosing_block
    implicit none
    integer :: value
    value = 7
10  continue
    block
20      continue
    end block
    if (value /= 7) error stop 1
end program
