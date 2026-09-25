! rule: S11.1.2.1-003
! covers: subroutine-reference-in-block-source, function-reference-in-block-source
program ab1121_procedure_refs
  implicit none
  integer :: sub_value, fun_value
  sub_value=-4; fun_value=-5
  block
    call set_value(sub_value)
    fun_value = add_seven(20)
  end block
  if (sub_value /= 64) then
    write(*,'(a)') 'SUBREF'
    error stop
  end if
  if (fun_value /= 27) then
    write(*,'(a)') 'FUNREF'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS PROCEDURE REFS OK'

contains
  subroutine set_value(arg)
    integer, intent(out) :: arg
    arg=64
  end subroutine set_value
  integer function add_seven(arg)
    integer, intent(in) :: arg
    add_seven=arg+7
  end function add_seven
end program ab1121_procedure_refs
