module eligibility_scope
  implicit none
contains
  subroutine declaration_context(subject)
    implicit none
    integer, allocatable, contiguous :: subject(..)
  end subroutine declaration_context
end module eligibility_scope
