module procedure_reference_15_5_1_definition_m
contains
  integer function module_add(n)
    integer, intent(in) :: n
    module_add = n + 6
  end function
  integer function module_alt(n)
    integer, intent(in) :: n
    module_alt = n + 60
  end function
end module procedure_reference_15_5_1_definition_m

integer function external_add(n)
  integer, intent(in) :: n
  external_add = n + 4
end function external_add

integer function external_alt(n)
  integer, intent(in) :: n
  external_alt = n + 40
end function external_alt

program procedure_reference_15_5_1_definition
  use procedure_reference_15_5_1_definition_m
  implicit none
  interface
    integer function external_add(n)
      integer, intent(in) :: n
    end function
    integer function external_alt(n)
      integer, intent(in) :: n
    end function
  end interface
  integer :: internal_value, module_value, external_value, checks
  checks = 0
  internal_value = -77
  module_value = -77
  external_value = -77
  internal_value = internal_add(5)
  if (internal_value /= 8) error stop 201
  checks = checks + 1
  module_value = module_add(5)
  if (module_value /= 11) error stop 202
  checks = checks + 1
  external_value = external_add(5)
  if (external_value /= 9) error stop 203
  checks = checks + 1
  if (checks /= 3) error stop 299
  print '(a)', 'PROCEDURE REFERENCE DEFINITION MECHANISMS OK'
contains
  integer function internal_add(n)
    integer, intent(in) :: n
    internal_add = n + 3
  end function
  integer function internal_alt(n)
    integer, intent(in) :: n
    internal_alt = n + 30
  end function
end program procedure_reference_15_5_1_definition
