! rule: S10.2.1.3-008
! covers: deferred-character-length zero-character-length fixed-parameter-control
! F2023 10.2.1.3 p3, bullet 2.
program s10_2_1_3_008_valid
    implicit none
    character(:), allocatable :: text
    character(5) :: fixed
    text = 'abc'
    if (.not. allocated(text)) error stop 'initial-allocation'
    if (len(text) /= 3 .or. text /= 'abc') error stop 'initial-length'
    text = 'vwxyz'
    if (len(text) /= 5 .or. text /= 'vwxyz') error stop 'changed-length'
    text(:) = 'q'
    if (len(text) /= 5) error stop 'substring-keeps-length'
    if (text /= 'q    ') error stop 'substring-padding'
    text = ''
    if (.not. allocated(text)) error stop 'zero-length-allocation'
    if (len(text) /= 0) error stop 'zero-length'
    fixed = 'ab'
    if (len(fixed) /= 5 .or. fixed /= 'ab   ') error stop 'fixed-length'
end program
