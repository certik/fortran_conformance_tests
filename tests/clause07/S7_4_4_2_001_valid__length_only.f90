! rule: S7.4.4.2-001
! covers: length-only-default-kind
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    character(3) :: positional
    character(len=3) :: keyword
    character*3 :: legacy
    character :: individual*3
    positional = 'ABC'
    keyword = 'DEF'
    legacy = 'ghi'
    individual = 'jkl'
    call check(positional, 'ABC')
    call check(keyword, 'DEF')
    call check(legacy, 'ghi')
    call check(individual, 'jkl')
contains
    subroutine check(text, expected)
        character(*), intent(in) :: text, expected
        if (kind(text) /= kind('A')) error stop 1
        if (len(text) /= 3 .or. text /= expected) error stop 2
    end subroutine
end program
