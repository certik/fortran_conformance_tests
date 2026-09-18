module optional_procedure_scope
  implicit none
  abstract interface
    subroutine signature()
    end subroutine signature
  end interface
contains
  subroutine declaration_context()
    implicit none
    procedure(signature), optional :: callback
  end subroutine declaration_context
end module optional_procedure_scope
