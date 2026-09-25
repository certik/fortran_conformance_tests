! rule: S11.1.2.1-001
! covers: procedure-return-exception-control
program ab1121_return_exception
  implicit none
  integer :: value
  value=3
  call inner(value)
  if (value /= 19) then
    write(*,'(a)') 'P1-RETURN'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS RETURN EXCEPTION OK'

contains
  subroutine inner(arg)
    integer, intent(inout) :: arg
    block
      arg=19
      return
    end block
    arg=-19
  end subroutine inner
end program ab1121_return_exception
