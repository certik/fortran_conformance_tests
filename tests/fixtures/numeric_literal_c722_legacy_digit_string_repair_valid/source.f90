! standard: f2023
! profile: absent-real-kind-seven
! C722 (R714) The value of kind-param shall specify an approximation method
! that exists on the processor.
! The profile establishes that kind 7 is absent before these cases are compiled.
subroutine c722_digit_string()
    implicit none
    real :: r
    r = 1.0   ! {error C722 digit-string}
end subroutine
