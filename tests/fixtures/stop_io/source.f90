program stop_io
    implicit none
    integer :: input, unit
    read(*, *) input
    write(*, '(a,ss,i0)') 'INPUT=', input
    open(newunit=unit, file='result.txt', status='new', action='write')
    write(unit, '(ss,i0)') input * input
    close(unit)
    stop 200
    write(*, '(a)') 'UNREACHABLE'
end program
