! rule: R702
! covers: enum
! evidence: positive-control
! standard: f2023
program r702_enum
    implicit none
    enum, bind(c) :: tone
        enumerator :: low = 2, high = 5
    end enum
    type(tone) :: values(2)
    values = [tone :: tone(low), tone(high)]
    if (size(values) /= 2) error stop 'size'
    if (values(1) /= tone(2)) error stop 'first'
    if (values(2) /= tone(5)) error stop 'second'
end program
