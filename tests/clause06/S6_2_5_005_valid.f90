! rule: S6.2.5-005
! covers: executable-statement nonexecutable-statement program-boundaries
! evidence: positive-control
1   program label_complete_statements
2       implicit none
3       integer :: value
4       value = 7
        if (value /= 7) error stop 1
5   end program
