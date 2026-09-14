! rule: C710
! covers: typeof-prior-type-parameters
! evidence: positive-control
! standard: f2023
program c710_typeof_prior
    implicit none
    character(kind=kind('a'), len=3) :: seed
    typeof(seed) :: copy
    seed = 'abc'
    copy = 'def'
    if (len(copy) /= 3 .or. kind(copy) /= kind('a')) error stop 'parameters'
    if (seed /= 'abc' .or. copy /= 'def') error stop 'values'
end program
