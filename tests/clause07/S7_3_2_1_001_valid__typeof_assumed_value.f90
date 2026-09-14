! rule: S7.3.2.1-001
! covers: typeof-assumed-value
! evidence: effect
! standard: f2023
program typeof_assumed_value
    implicit none
    character(8) :: storage
    storage = '--------'
    call fill('abc', storage)
    if (storage /= 'Z  -----') error stop 'length-three-sentinels'
    storage = '--------'
    call fill('abcde', storage)
    if (storage /= 'Z    ---') error stop 'length-five-sentinels'
contains
    subroutine fill(seed, copy)
        character(*), intent(in) :: seed
        typeof(seed), intent(inout) :: copy
        if (len(copy) /= len(seed)) error stop 'value-not-assumed'
        copy = 'Z'
    end subroutine
end program
