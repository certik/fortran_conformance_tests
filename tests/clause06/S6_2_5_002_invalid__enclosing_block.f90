! rule: S6.2.5-002
! covers: enclosing-block-scope
! case: host-and-block
program label_enclosing_block
    implicit none
    integer :: value
    value = 7
10  continue
    block
10      continue ! {error S6.2.5-002 host-and-block}
    end block
    if (value /= 7) error stop 1
end program
