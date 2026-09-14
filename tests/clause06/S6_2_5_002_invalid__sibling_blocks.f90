! rule: S6.2.5-002
! covers: sibling-block-scopes
! case: sibling-blocks
program label_sibling_blocks
    implicit none
    integer :: value
    value = 7
    block
10      continue
    end block
    block
10      continue ! {error S6.2.5-002 sibling-blocks}
    end block
    if (value /= 7) error stop 1
end program
