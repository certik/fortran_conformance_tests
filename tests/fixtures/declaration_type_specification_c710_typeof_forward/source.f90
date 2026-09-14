program c710_typeof_prior
    implicit none
    typeof(seed) :: copy
    character(kind=kind('a'), len=3) :: seed
    seed = 'abc'
    copy = 'def'
    if (len(copy) /= 3 .or. kind(copy) /= kind('a')) error stop 'parameters'
    if (seed /= 'abc' .or. copy /= 'def') error stop 'values'
end program
