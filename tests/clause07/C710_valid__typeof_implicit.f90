! rule: C710
! covers: typeof-implicit
! evidence: positive-control
! standard: f2023
program c710_typeof_implicit
    implicit integer(i-n)
    typeof(number) :: copy
    number = 3
    copy = 7
    if (kind(copy) /= kind(0)) error stop 'kind'
    if (number /= 3 .or. copy /= 7) error stop 'values'
end program
