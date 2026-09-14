! rule: C704
! covers: named-derived-parameters
! evidence: positive-control
program c704_named_parameters
    implicit none
    type :: packet(k, n)
        integer, kind :: k = kind(0)
        integer, len :: n
        integer(k) :: code
        character(n) :: text
    end type
    type(packet(n=3)) :: value
    value%code = 7
    value%text = 'abc'
    if (value%k /= kind(0) .or. value%n /= 3) error stop 'parameters'
    if (kind(value%code) /= kind(0)) error stop 'component-kind'
    if (len(value%text) /= 3) error stop 'component-length'
    if (value%code /= 7 .or. value%text /= 'abc') error stop 'values'
end program
