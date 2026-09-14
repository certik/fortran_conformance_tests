! rule: S6.2.5-006
! covers: forward-branch backward-branch
program label_branch_targets
    implicit none
    integer :: visits
    visits = 0
    go to 20
    error stop 1
10  visits = visits + 1
    if (visits < 3) go to 10
    go to 30
20  visits = 0
    go to 10
30  if (visits /= 3) error stop 2
end program
