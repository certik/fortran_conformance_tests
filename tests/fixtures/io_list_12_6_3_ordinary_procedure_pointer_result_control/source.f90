program io_list_ordinary_procedure_pointer_result_control
  implicit none
  abstract interface
    integer function f()
    end function f
  end interface
  integer :: checks
  procedure(f), pointer :: p
  character(len=4) :: out
  checks = 0
  p => value
  out = '####'
  write(out,'(SS,I2)') p()
  if (out /= '12  ') error stop 'procedure pointer result output'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ORDINARY_PROCEDURE_POINTER_RESULT_CONTROL OK'
contains
  integer function value()
    value = 12
  end function value
end program io_list_ordinary_procedure_pointer_result_control
