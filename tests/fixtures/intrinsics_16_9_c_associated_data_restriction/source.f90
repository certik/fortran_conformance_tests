module i169c_assoc_data_restriction_mod
  implicit none
  integer, target :: module_target = 37
contains
  function pointer_function() result(result_pointer)
    integer, pointer :: result_pointer
    result_pointer => module_target
  end function pointer_function
end module i169c_assoc_data_restriction_mod
program i169c_associated_data_restriction
  use i169c_assoc_data_restriction_mod
  implicit none
  integer, target :: scalar_target = 37
  integer, target :: array_target(3) = [1, 2, 3]
  integer, pointer :: scalar_pointer
  integer, pointer :: array_pointer(:)
  scalar_pointer => scalar_target
  array_pointer => array_target
  call require_true('targetable scalar positive control true', associated(scalar_pointer, scalar_target))
  scalar_pointer => module_target
  call require_true('data pointer function result true', associated(scalar_pointer, pointer_function()))
  call require_true('whole array no vector subscript true', associated(array_pointer, array_target))
  call require_true('same integer kind target true', kind(scalar_pointer) == kind(scalar_target))
  call require_true('same rank array target true', rank(array_pointer) == rank(array_target))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED DATA RESTRICTION OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169c_associated_data_restriction
