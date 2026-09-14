! rule: S7.3.2.2-002
! covers: body-local-derived-result
! evidence: effect
program type_body_derived
    implicit none
    character(len=16) :: record = 'not-written'
    integer :: ios = -1
    write(record, '(ss,i0)', iostat=ios) make()
    if (ios /= 0) error stop 'result-output'
    if (trim(record) /= '41') error stop 'body-result-value'
contains
    type(local_packet) function make() result(r)
        type :: local_packet
            integer :: tag
        end type
        r%tag = 41
    end function
end program
