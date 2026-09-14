! rule: C603
! covers: all-zero-definition
! evidence: positive-control
program label_zero_repairs
    implicit none
    integer :: visits
    visits = 0
    call one
    call two
    call three
    call four
    call five
    if (visits /= 5) error stop 1
contains
    subroutine one
1       continue
        visits = visits + 1
    end subroutine
    subroutine two
01      continue
        visits = visits + 1
    end subroutine
    subroutine three
001     continue
        visits = visits + 1
    end subroutine
    subroutine four
0001    continue
        visits = visits + 1
    end subroutine
    subroutine five
00001   continue
        visits = visits + 1
    end subroutine
end program
